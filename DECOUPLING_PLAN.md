# Architecture Decoupling Plan

## **DIAGNOSIS: Why "Whack-a-Mole" Regressions Occur**

### **Root Causes Identified:**

1. **God Classes** - `AIService` (1432 lines) does too much
2. **Tight Coupling** - Services instantiate their own dependencies
3. **Brittle Regex Logic** - Mermaid validation scattered and untested
4. **No Test Safety Net** - No regression suite to catch breaks
5. **Frontend/Backend Coupling** - Streaming logic duplicated

---

## **ARCHITECTURE REDESIGN**

### **Phase 1: Extract Core Components (Backend)**

#### **1.1 Create Core Module Structure**
```
backend/app/
├── core/
│   ├── container.py          # NEW: Dependency injection container
│   └── interfaces.py          # NEW: Abstract base classes
├── services/
│   ├── llm/                   # NEW: LLM-specific logic
│   │   ├── provider.py        # Multi-provider routing
│   │   ├── mistral_client.py  # Mistral-specific
│   │   └── nvidia_client.py   # NVIDIA-specific
│   ├── rag/                   # EXISTING: Already decent
│   │   └── enhanced_rag.py
│   ├── tools/                 # EXISTING: External APIs
│   │   ├── biomedical.py
│   │   └── web_search.py
│   └── postprocessing/        # NEW: Response processing
│       ├── mermaid.py         # Centralized Mermaid logic
│       ├── markdown.py        # Markdown fixes
│       └── safety.py          # Security guard
├── utils/
│   └── test_helpers.py        # NEW: Test utilities
```

#### **1.2 Dependency Injection Container**
```python
# backend/app/core/container.py
from typing import Optional
from supabase import Client

class ServiceContainer:
    """Centralized service registry - Single Source of Truth"""
    
    _instance: Optional['ServiceContainer'] = None
    _services: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, db: Client):
        """Initialize all services ONCE"""
        self.db = db
        self._services = {
            'llm_provider': MultiProviderLLM(db),
            'rag_service': EnhancedRAGService(db),
            'chat_service': ChatService(db),
            'mermaid_processor': MermaidProcessor(),
            'safety_guard': LLMSecurityGuard(),
        }
        return self
    
    def get(self, service_name: str):
        """Get service instance - NO direct instantiation"""
        if service_name not in self._services:
            raise KeyError(f"Service {service_name} not registered")
        return self._services[service_name]

# Global singleton
container = ServiceContainer()
```

#### **1.3 Interface Definitions**
```python
# backend/app/core/interfaces.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class LLMProvider(ABC):
    """Abstract LLM interface - swappable implementations"""
    
    @abstractmethod
    async def generate(self, messages: list, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_stream(self, messages: list, **kwargs) -> AsyncGenerator[str, None]:
        pass

class MermaidProcessor(ABC):
    """Abstract Mermaid processing interface"""
    
    @abstractmethod
    def validate_and_fix(self, mermaid_code: str) -> tuple[str, list, list]:
        pass
```

---

### **Phase 2: Centralize Brittle Logic**

#### **2.1 Mermaid Processing Module**
```python
# backend/app/services/postprocessing/mermaid.py
"""
Centralized Mermaid Diagram Processing
ALL Mermaid logic lives here - tested once, used everywhere
"""

import re
from typing import Tuple, List
from app.core.interfaces import MermaidProcessor

class MermaidProcessorImpl(MermaidProcessor):
    """Production Mermaid processor with comprehensive fixes"""
    
    # UNICODE NORMALIZATION MAP (centralized, tested)
    UNICODE_FIXES = {
        '\u2011': '-',  # Non-breaking hyphen
        '\u00a0': ' ',  # Non-breaking space
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '≥': '__GE__',  # Greater-equal (protected)
        '≤': '__LE__',  # Less-equal (protected)
        '×': 'x',       # Multiplication
        '÷': '/',       # Division
    }
    
    # ARROW PATTERNS (centralized, tested)
    VALID_ARROWS = ['<-->', '<--', '-->', '--', '==>', '..', '.->']
    
    def validate_and_fix(self, mermaid_code: str) -> Tuple[str, List[str], List[str]]:
        """
        Validate and fix Mermaid syntax.
        Returns: (corrected_code, errors, warnings)
        """
        errors, warnings = [], []
        
        # Step 1: Unicode normalization
        corrected = self._normalize_unicode(mermaid_code)
        
        # Step 2: Structural fixes
        corrected = self._fix_structure(corrected, warnings)
        
        # Step 3: Restore protected sequences
        corrected = self._restore_protected(corrected)
        
        # Step 4: Validation
        is_valid, validation_errors = self._validate(corrected)
        errors.extend(validation_errors)
        
        return corrected, errors, warnings
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters to ASCII equivalents"""
        for unicode_char, replacement in self.UNICODE_FIXES.items():
            text = text.replace(unicode_char, replacement)
        return text
    
    def _restore_protected(self, text: str) -> str:
        """Restore protected sequences after processing"""
        text = text.replace('__GE__', '>=')
        text = text.replace('__LE__', '<=')
        return text
    
    # ... rest of implementation

# Export singleton instance
mermaid_processor = MermaidProcessorImpl()
```

#### **2.2 Usage in AIService (Decoupled)**
```python
# backend/app/services/ai.py (REFACTORED)
from app.core.container import container
from app.services.postprocessing.mermaid import mermaid_processor

class AIService:
    def __init__(self, db: Client = None):
        # Get services from container - NO direct instantiation
        self.container = container.initialize(db) if db else container
        self.llm = self.container.get('llm_provider')
        self.rag = self.container.get('rag_service')
        self.chat = self.container.get('chat_service')
        self.mermaid = self.container.get('mermaid_processor')  # Centralized!
        self.safety = self.container.get('safety_guard')
    
    async def generate_streaming_response(self, ...):
        # ... generation logic ...
        
        # Post-process with centralized Mermaid processor
        if '```mermaid' in full_response:
            corrected, errors, warnings = self.mermaid.validate_and_fix(
                extract_mermaid(full_response)
            )
            full_response = replace_mermaid(full_response, corrected)
        
        return full_response
```

---

### **Phase 3: Frontend Decoupling**

#### **3.1 Extract Streaming Logic**
```typescript
// frontend/src/lib/streaming/TokenStreamer.ts
/**
 * Centralized streaming logic - decoupled from useChat
 */
export class TokenStreamer {
  private buffer: string[] = [];
  private isStreaming = false;
  private onComplete?: () => void;

  constructor(
    private onToken: (token: string) => void,
    private onError?: (error: Error) => void
  ) {}

  async streamFromSSE(eventSource: EventSource): Promise<void> {
    this.isStreaming = true;
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        this.flush();
        this.isStreaming = false;
        this.onComplete?.();
        return;
      }
      
      const data = JSON.parse(event.data);
      if (data.text) {
        this.buffer.push(data.text);
        this.flush();
      }
    };
    
    eventSource.onerror = (error) => {
      this.onError?.(error);
      this.isStreaming = false;
    };
  }

  private flush() {
    if (this.buffer.length > 0) {
      const content = this.buffer.join('');
      this.buffer = [];
      this.onToken(content);
    }
  }
}
```

#### **3.2 Simplified useChat Hook**
```typescript
// frontend/src/hooks/useChat.ts (REFACTORED)
import { TokenStreamer } from '@/lib/streaming/TokenStreamer';
import { useChatState } from './useChatState';
import { useChatActions } from './useChatActions'; // NEW: Extracted actions

export function useChat() {
  const state = useChatState();
  const actions = useChatActions(state);
  
  // Streaming is now a separate concern
  const streamer = useMemo(() => 
    new TokenStreamer(
      (token) => state.appendToken(token),
      (error) => actions.handleError(error)
    ),
    [state, actions]
  );

  const sendMessage = useCallback(async (content: string, mode: Mode) => {
    // 1. Save user message
    const userMsg = await actions.saveUserMessage(content);
    
    // 2. Start streaming
    const eventSource = await actions.initiateStream(content, mode);
    await streamer.streamFromSSE(eventSource);
    
    return userMsg;
  }, [actions, streamer]);

  return {
    ...state,
    ...actions,
    sendMessage,
  };
}
```

---

### **Phase 4: Regression Test Suite**

#### **4.1 Backend Test Structure**
```python
# backend/tests/regression/
├── test_mermaid_processing.py    # Centralized Mermaid tests
├── test_llm_routing.py            # Provider failover tests
├── test_rag_context.py            # RAG retrieval tests
└── test_safety_guard.py           # Security tests

# backend/tests/regression/test_mermaid_processing.py
import pytest
from app.services.postprocessing.mermaid import mermaid_processor

class TestMermaidProcessing:
    """Comprehensive Mermaid processing tests - run in <100ms"""
    
    def test_unicode_normalization(self):
        """Test Unicode character fixes"""
        broken = "A -->|≥15%| B"
        fixed, errors, warnings = mermaid_processor.validate_and_fix(broken)
        assert '>=' in fixed
        assert len(errors) == 0
    
    def test_parentheses_balancing(self):
        """Test parentheses in labels"""
        broken = 'A["Drug(10-14 days"] --> B["Effect"]'
        fixed, errors, warnings = mermaid_processor.validate_and_fix(broken)
        assert fixed.count('(') == fixed.count(')')
    
    def test_arrow_normalization(self):
        """Test arrow pattern fixes"""
        broken = "A ->> B"
        fixed, errors, warnings = mermaid_processor.validate_and_fix(broken)
        assert '-->' in fixed
    
    def test_full_diagram(self):
        """Test complete diagram from production"""
        broken = '''
        flowchart TD
            A["Clarithromycin 10‑14 d"]
            B -->|≥15%| C["Resistance"]
        '''
        fixed, errors, warnings = mermaid_processor.validate_and_fix(broken)
        assert errors == []
        assert 'flowchart TD' in fixed
```

#### **4.2 Frontend Test Structure**
```typescript
// frontend/src/tests/regression/
├── test_token_streamer.test.ts    # Streaming logic tests
├── test_mermaid_render.test.ts    # Mermaid rendering tests
└── test_chat_state.test.ts        # State management tests

// frontend/src/tests/regression/test_token_streamer.test.ts
import { describe, it, expect, vi } from 'vitest';
import { TokenStreamer } from '@/lib/streaming/TokenStreamer';

describe('TokenStreamer', () => {
  it('buffers and flushes tokens correctly', () => {
    const onToken = vi.fn();
    const streamer = new TokenStreamer(onToken);
    
    streamer.buffer.push('Hello');
    streamer.buffer.push(' ');
    streamer.buffer.push('World');
    streamer.flush();
    
    expect(onToken).toHaveBeenCalledWith('Hello World');
  });
  
  it('handles SSE done signal', async () => {
    const onComplete = vi.fn();
    const streamer = new TokenStreamer(vi.fn(), undefined);
    streamer.onComplete = onComplete;
    
    // Simulate [DONE] signal
    streamer.isStreaming = true;
    // ... simulate done
    expect(onComplete).toHaveBeenCalled();
  });
});
```

#### **4.3 Fast Regression Suite Command**
```bash
# backend/tests/run_regression.sh
#!/bin/bash
echo "🧪 Running Backend Regression Suite..."
time pytest tests/regression/ -v --tb=short

# frontend/package.json
{
  "scripts": {
    "test:regression": "vitest run src/tests/regression/"
  }
}

# Combined command for CI/CD
npm run test:regression && cd backend && pytest tests/regression/
```

---

## **IMPLEMENTATION PRIORITY**

### **Week 1: Critical Fixes**
1. ✅ Create `ServiceContainer` (breaks circular dependencies)
2. ✅ Extract `MermaidProcessor` (centralizes brittle logic)
3. ✅ Add regression tests for Mermaid (catches breaks immediately)

### **Week 2: LLM Decoupling**
1. Extract `MultiProviderLLM` from `AIService`
2. Create `LLMProvider` interface
3. Add provider routing tests

### **Week 3: Frontend Decoupling**
1. Extract `TokenStreamer` class
2. Simplify `useChat` hook
3. Add streaming tests

### **Week 4: Full Test Coverage**
1. RAG context tests
2. Safety guard tests
3. Integration tests
4. CI/CD pipeline integration

---

## **EXPECTED OUTCOMES**

### **Before Refactoring:**
- ❌ Fix one thing, break another
- ❌ 1400+ line God classes
- ❌ No test safety net
- ❌ Brittle regex scattered everywhere

### **After Refactoring:**
- ✅ Isolated changes don't cascade
- ✅ <200 line focused modules
- ✅ <5 second regression suite
- ✅ Centralized, tested brittle logic

---

## **METRICS FOR SUCCESS**

| Metric | Before | Target |
|--------|--------|--------|
| `AIService` lines | 1432 | <400 |
| Regression test time | N/A | <10s |
| Circular dependencies | 1 | 0 |
| Test coverage | ~20% | >80% |
| Time to detect regression | Production | Pre-commit |
