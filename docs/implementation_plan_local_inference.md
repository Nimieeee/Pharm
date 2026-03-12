# Local Inference & Intelligent Routing — Implementation Plan

> **Scope**: Self-hosted BitNet on AWS Lightsail VPS with intelligent prompt routing
> **Total Effort**: ~30-40 hours
> **Dependencies**: None from Year 1 plan (can run in parallel)

---

## 1. VPS Hardware Analysis

Your current VPS from `CLAUDE.md`:

| Spec | Value | Implication |
|------|-------|-------------|
| **Platform** | AWS Lightsail | Shared tenancy, burstable CPU |
| **vCPUs** | 2 | Single-user inference only; queuing needed for concurrency |
| **RAM** | 8 GB | ~5 GB budget for model after OS + FastAPI + PostgreSQL |
| **CPU Type** | Intel Xeon E5-2676 v3 or Platinum 8259CL | **AVX2 ✅** (required by bitnet.cpp) |
| **Architecture** | x86_64 | ✅ (bitnet.cpp has ARM Linux bug) |
| **OS** | Ubuntu | ✅ |
| **Disk** | SSD (Lightsail default) | Model files load fast from disk |

### RAM Budget Breakdown

```
Total RAM:                           8,192 MB
─────────────────────────────────────────────
Ubuntu OS + systemd:                  -500 MB
PostgreSQL (Supabase local cache):    -200 MB
FastAPI + PM2 (benchside-api):        -300 MB
Safety buffer (swap prevention):      -500 MB
─────────────────────────────────────────────
Available for model:                ~6,692 MB
```

---

## 2. Model Selection Matrix

| Model | Weights RAM | 8k KV Cache (4-bit) | Total RAM | Fits? | Output Quality |
|-------|-----------|-------------------|-----------|-------|---------------|
| BitNet b1.58 **2B4T** | ~1.3 GB | ~64 MB | **~1.4 GB** | ✅ Easily | Good for definitions, lookups |
| BitNet b1.58 **8B** (Llama3 converted) | ~4.1 GB | ~256 MB | **~4.4 GB** | ✅ Comfortable | Strong reasoning, medical Q&A |
| BitNet b1.58 **13B** | ~6.5 GB | ~400 MB | **~6.9 GB** | ⚠️ Tight | Excellent, near-70B quality |
| BitNet b1.58 **70B** | ~14 GB | ~2 GB | **~16 GB** | ❌ Impossible | N/A |

### Recommendation: **Dual-Model Strategy**

Load **both** the 2B and 8B models simultaneously:
- 2B (1.4 GB) + 8B (4.4 GB) = **~5.8 GB** — fits within budget
- Simple prompts → 2B (instant response, <100ms/token)
- Complex prompts → 8B (detailed reasoning, ~300ms/token)
- If RAM is tight, fall back to 8B-only (4.4 GB)

---

## 3. Serving Architecture

### How bitnet.cpp Serves Models

bitnet.cpp is built on top of `llama.cpp`. Models are converted to **GGUF format** and served via `llama.cpp`'s built-in HTTP server, which exposes an **OpenAI-compatible `/v1/chat/completions` endpoint**.

This means: **zero custom HTTP code**. We treat the local server as just another provider in `multi_provider.py`.

```
┌─────────────────────────────────────────────────────┐
│                    VPS (8GB RAM)                     │
│                                                     │
│  ┌──────────────┐     ┌─────────────────────────┐   │
│  │  FastAPI      │────▶│ llama.cpp server         │   │
│  │  (Port 7860)  │     │ (Port 8080)              │   │
│  │              │     │ BitNet 8B GGUF            │   │
│  │  multi_      │     │ OpenAI-compatible API     │   │
│  │  provider.py │     │ /v1/chat/completions      │   │
│  └──────────────┘     └─────────────────────────┘   │
│                                                     │
│  RAM: ~300MB FastAPI + ~4.4GB Model = ~4.7GB        │
└─────────────────────────────────────────────────────┘
```

### RoPE Scaling to 8k

The default BitNet 8B context is 4,096 tokens. To reach 8,192:

```bash
# Launch with RoPE scaling
./llama-server \
  --model bitnet-8b.gguf \
  --host 0.0.0.0 --port 8080 \
  --ctx-size 8192 \
  --rope-scaling linear \
  --rope-scale 2.0 \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  --threads 2 \
  --n-predict 4096
```

**Flags explained:**
- `--ctx-size 8192`: Total context window (input + output)
- `--rope-scaling linear --rope-scale 2.0`: Doubles the native 4k to 8k
- `--cache-type-k q4_0 --cache-type-v q4_0`: 4-bit KV cache (saves ~75% cache RAM)
- `--threads 2`: Match your 2 vCPUs
- `--n-predict 4096`: Max output tokens per request

---

## 4. Intelligent Router (Mode + Complexity Hybrid)

The user manually selects **Fast**, **Detailed**, or **Elite** mode in the UI. Within each mode, a **complexity scorer** analyzes the prompt to decide whether the local model is "good enough" or whether to escalate to a more powerful remote model.

### 4.1 Complexity Scorer

```python
class PromptComplexityScorer:
    """Scores prompt complexity 0.0-1.0 to decide local vs remote."""
    
    COMPLEX_SIGNALS = [
        "review", "synthesize", "comprehensive", "compare and contrast",
        "systematic", "meta-analysis", "literature", "in-depth",
        "all aspects", "thorough", "detailed analysis"
    ]
    
    PRIVACY_SIGNALS = [
        "patient", "genotype", "rs", "CYP", "HLA-", "allele",
        "my results", "my data", "confidential", "HIPAA"
    ]
    
    def score(self, prompt: str, token_count: int) -> float:
        score = 0.0
        score += min(token_count / 3000, 0.3)
        matches = sum(1 for kw in self.COMPLEX_SIGNALS if kw in prompt.lower())
        score += min(matches * 0.1, 0.4)
        score += min(prompt.count("?") * 0.05, 0.15)
        return min(score, 1.0)
    
    def is_private(self, prompt: str) -> bool:
        return any(kw in prompt.lower() for kw in self.PRIVACY_SIGNALS)
```

### 4.2 Per-Mode Escalation Logic

```python
class ModeRouter:
    """Routes within user-selected mode based on complexity."""
    
    def __init__(self):
        self.scorer = PromptComplexityScorer()
        self.local_queue = LocalInferenceQueue()
    
    def route(self, prompt: str, token_count: int, mode: str) -> str:
        complexity = self.scorer.score(prompt, token_count)
        is_private = self.scorer.is_private(prompt)
        queue_busy = self.local_queue.is_busy()
        
        if mode == "fast":
            return self._route_fast(complexity, queue_busy)
        elif mode == "detailed":
            return self._route_detailed(complexity, is_private, queue_busy)
        elif mode == "elite":
            return self._route_elite()
    
    def _route_fast(self, complexity: float, queue_busy: bool) -> str:
        if complexity < 0.3 and not queue_busy:
            return "local_2b"          # BitNet 2B — instant, free
        elif complexity < 0.6:
            return "groq_8b"           # Groq Llama 3.1 8B — fast remote
        else:
            return "sonnet_4_6"        # Sonnet 4.6 — complex but user wants speed
    
    def _route_detailed(self, complexity: float, is_private: bool, 
                        queue_busy: bool) -> str:
        if is_private:
            return "local_8b"          # Privacy: data never leaves VPS
        if complexity < 0.4 and not queue_busy:
            return "local_8b"          # BitNet 8B — decent reasoning, free
        else:
            return "sonnet_4_6"        # Sonnet 4.6 — superior reasoning
    
    def _route_elite(self) -> str:
        return "sonnet_4_6"            # Always Sonnet 4.6 (1M ctx, best reasoning)
        # Fallback (if Sonnet is down): step-3.5-flash
```

### 4.3 Routing Summary Table

| Mode | Complexity | Decision | Model | Cost |
|:---|:---|:---|:---|:---|
| **Fast** | Low (< 0.3) | Local handles it | **BitNet 2B** | $0.00 |
| **Fast** | Medium (0.3-0.6) | Escalate to Groq | **Groq 8B** | free tier |
| **Fast** | High (> 0.6) | Escalate to Sonnet | **Sonnet 4.6** | 0.01/M |
| **Detailed** | Privacy detected | Force local | **BitNet 8B** | $0.00 |
| **Detailed** | Low-Medium (< 0.4) | Local handles it | **BitNet 8B** | $0.00 |
| **Detailed** | High (> 0.4) | Escalate to Sonnet | **Sonnet 4.6** | 0.01/M |
| **Elite** | Any | Always Sonnet | **Sonnet 4.6** | 0.01/M |
| **Elite** | Sonnet down | Fallback | **Step 3.5 Flash** | 0.01/M |

### 4.4 Integration with `multi_provider.py`

```python
# Add to Provider enum
class Provider(Enum):
    MISTRAL = "mistral"
    GROQ = "groq"
    NVIDIA = "nvidia"
    POLLINATIONS = "pollinations"
    LOCAL = "local"           # NEW

# MODE_PRIORITIES — fallback chain per mode
MODE_PRIORITIES = {
    "fast": [Provider.LOCAL, Provider.GROQ, Provider.POLLINATIONS],
    "detailed": [Provider.POLLINATIONS, Provider.LOCAL, Provider.NVIDIA],
    "deep_research": [Provider.POLLINATIONS, Provider.NVIDIA, Provider.GROQ],
    "deep_research_elite": [Provider.POLLINATIONS],
    "deep_research_single_pass": [Provider.GROQ],
}

# LOCAL provider config
if os.getenv("LOCAL_MODEL_ENABLED", "false") == "true":
    self.providers[Provider.LOCAL] = ProviderConfig(
        name=Provider.LOCAL,
        api_key="not-needed",
        base_url="http://localhost:8080/v1",
        models={
            "fast": "bitnet-2b",
            "detailed": "bitnet-8b",
        },
        headers={"Content-Type": "application/json"},
        weight=1.0,
        rpm_limit=999,
    )

# POLLINATIONS provider models (update existing config)
models={
    "fast": "claude-airforce",           # Sonnet 4.6 — escalation target for fast
    "detailed": "claude-airforce",       # Sonnet 4.6 — escalation target for detailed
    "deep_research": "claude-airforce",  # Sonnet 4.6 — elite primary
    "deep_research_elite": "step-3.5-flash",  # Step 3.5 Flash — elite fallback
}
```

---

## 5. Concurrency & Queuing

### The Problem
With 2 vCPUs, the BitNet model can only process **1 request at a time** efficiently. A second concurrent request would halve the speed for both users.

### The Solution: Request Queue

```python
class LocalInferenceQueue:
    """Serializes requests to the local model to prevent CPU contention."""
    
    def __init__(self, max_queue_size: int = 5):
        self._semaphore = asyncio.Semaphore(1)  # 1 concurrent request
        self._queue_size = 0
        self._max_queue = max_queue_size
    
    async def submit(self, request_fn):
        if self._queue_size >= self._max_queue:
            raise HTTPException(503, "Local model queue full, try remote mode")
        
        self._queue_size += 1
        try:
            async with self._semaphore:
                return await request_fn()
        finally:
            self._queue_size -= 1
```

**User experience:**
- User 1 sends prompt → starts immediately
- User 2 sends prompt while User 1 is generating → queued, sees "Position 1 in queue" toast
- If 5+ users are waiting → auto-fallback to remote provider (Groq/NVIDIA)

---

## 6. UI/UX Changes

### 6.1 Queue Position Toast

When queued behind another user:
```
"Your request is queued (position 2). Estimated wait: ~15s"
```
Uses existing `sonner` toast system.

---

## 7. VPS Setup & Deployment

### 7.1 One-Time Setup Script

```bash
#!/bin/bash
# deploy_bitnet.sh — Run on VPS via SSH

# 1. Install build dependencies
sudo apt update && sudo apt install -y cmake build-essential git

# 2. Clone and build bitnet.cpp
cd /opt
sudo git clone --recursive https://github.com/microsoft/BitNet.git
cd BitNet
sudo mkdir build && cd build
sudo cmake .. -DCMAKE_BUILD_TYPE=Release
sudo cmake --build . --config Release -j2

# 3. Download model (8B, ~4.1GB)
sudo mkdir -p /opt/models
cd /opt/models
# Download from HuggingFace (exact URL depends on available model)
sudo wget https://huggingface.co/1bitLLM/bitnet_b1_58-3B/resolve/main/model.gguf \
  -O bitnet-model.gguf

# 4. Create systemd service
sudo tee /etc/systemd/system/bitnet.service > /dev/null <<EOF
[Unit]
Description=BitNet Local Inference Server
After=network.target

[Service]
Type=simple
ExecStart=/opt/BitNet/build/bin/llama-server \
  --model /opt/models/bitnet-model.gguf \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 8192 \
  --rope-scaling linear --rope-scale 2.0 \
  --cache-type-k q4_0 --cache-type-v q4_0 \
  --threads 2 --n-predict 4096
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable bitnet
sudo systemctl start bitnet
```

### 7.2 Environment Variable

Add to VPS `.env`:
```
LOCAL_MODEL_ENABLED=true
LOCAL_MODEL_URL=http://127.0.0.1:8080/v1
```

### 7.3 Health Check

```bash
# Add to PM2 ecosystem or cron
curl -s http://127.0.0.1:8080/health | jq .status
# Expected: "ok"
```

---

## 8. File Changes Summary

### Backend (4 files)

| Action | File | What Changes |
|--------|------|-------------|
| MODIFY | `backend/app/services/multi_provider.py` | Add `Provider.LOCAL`, `ProviderConfig` for localhost:8080, update `MODE_PRIORITIES` |
| NEW | `backend/app/services/router_service.py` | `PromptComplexityScorer` + `ModeRouter` classes with per-mode escalation |
| NEW | `backend/app/services/local_queue.py` | `LocalInferenceQueue` with semaphore-based serialization |
| MODIFY | `backend/app/core/config.py` | Add `LOCAL_MODEL_ENABLED`, `LOCAL_MODEL_URL` settings |

### Frontend (1 file)

| Action | File | What Changes |
|--------|------|-------------|
| MODIFY | `frontend/src/components/chat/ChatInput.tsx` | Queue position toast when local model is busy |

### Infrastructure (2 files)

| Action | File | What Changes |
|--------|------|-------------|
| NEW | `scripts/deploy_bitnet.sh` | VPS setup script (build, download, systemd service) |
| MODIFY | `backend/.env.example` | Add `LOCAL_MODEL_ENABLED`, `LOCAL_MODEL_URL` |

---

## 9. Verification Plan

### Automated Tests

```bash
# Test router classification logic
pytest tests/test_router_service.py -v
# Tests:
#   - Fast mode + simple prompt → routes to LOCAL (BitNet 2B)
#   - Fast mode + complex prompt → routes to GROQ (Llama 3.1 8B)
#   - Fast mode + local queue full → falls back to GROQ
#   - Detailed mode + privacy prompt ("My CYP2D6 genotype...") → routes to LOCAL (BitNet 8B)
#   - Detailed mode + standard prompt → routes to POLLINATIONS (Sonnet 4.6)
#   - Elite mode → routes to POLLINATIONS (Sonnet 4.6)
#   - Elite mode + Sonnet 4.6 down → falls back to Step 3.5 Flash

# Test queue behavior
pytest tests/test_local_queue.py -v
# Tests:
#   - Single request passes through immediately
#   - 6th concurrent request raises 503
#   - Queue drains correctly after completion

# Test multi_provider LOCAL integration
pytest tests/test_multi_provider_unit.py -v
# Tests:
#   - LOCAL provider registered when env var set
#   - LOCAL provider NOT registered when env var unset
#   - MODE_PRIORITIES include LOCAL for fast/detailed
```

### Manual Verification (on VPS)

1. SSH into VPS, run `deploy_bitnet.sh`
2. Verify model server: `curl http://127.0.0.1:8080/v1/models`
3. Test inference: Send a prompt via curl to the local endpoint
4. Restart `benchside-api` with `LOCAL_MODEL_ENABLED=true`
5. Select **Fast mode** → send "What is aspirin?" → verify routes to Local-2B
6. Select **Fast mode** → send a long complex prompt → verify routes to Groq
7. Select **Detailed mode** → send "Explain warfarin resistance" → verify routes to Sonnet 4.6
8. Select **Detailed mode** → send "My CYP2D6 genotype is *4/*4" → verify routes to Local-8B (privacy)
9. Select **Elite mode** → send "Systematic review of SGLT2 inhibitors" → verify routes to Sonnet 4.6

---

## 10. Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Model OOM on VPS | Low | High | 4-bit KV cache + RAM monitoring + auto-fallback to remote |
| CPU contention with FastAPI | Medium | Medium | Semaphore queue + `--threads 2` cap |
| RoPE quality degradation at 8k | Medium | Low | Test quality on medical benchmark before deploying |
| Lightsail CPU throttling (burstable) | Medium | Medium | Monitor CPU credits; sustained use may trigger throttle |
| bitnet.cpp instability | Low | Medium | systemd auto-restart + health check + remote fallback |

> [!WARNING]
> **Lightsail Burstable CPUs**: Your 2 vCPU plan uses burstable instances. Under sustained load (e.g., generating 4096 tokens for multiple users), AWS may throttle your CPU to baseline performance (~20% of burst). Monitor CPU credit balance in the Lightsail console. If this becomes an issue, upgrade to a 4 vCPU / 16GB plan (~$40/mo) which would also allow running the 13B model.

> [!NOTE]
> **Upgrade Path**: If you move to a 4 vCPU / 16GB RAM Lightsail instance (~$40/mo), you could run the **13B BitNet model** with a 16k context window. This would give near-70B quality entirely on your own hardware.
