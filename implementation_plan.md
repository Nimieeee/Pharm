# Multi-Provider AI Routing — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the already-built [MultiProviderService](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#46-344) into the main chat and deep research LLM call paths so all user-facing AI traffic routes through priority-based, health-aware multi-provider routing instead of hardcoded Mistral-only calls.

**Architecture:** [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py) is fully implemented with 3-provider routing (NVIDIA 80%, Groq 15%, Mistral 5%), priority-based mode selection, 429 detection/cooldown, and weighted fallback. However, [ai.py](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py) and [deep_research.py](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py) both bypass it entirely, making direct HTTP calls to Mistral's API. The task is to replace those direct calls with [multi_provider](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#349-354) delegation.

**Tech Stack:** Python 3.11, FastAPI, httpx, pydantic-settings

---

## Gap Analysis

> [!IMPORTANT]
> The [MultiProviderService](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#46-344) class in [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py) is **fully built and tested** (2,997 lines of property-based tests in [test_multi_provider_properties.py](file:///Users/mac/Desktop/phhh/backend/tests/test_multi_provider_properties.py)) but is **not wired into the actual code paths**. The import `from app.services.multi_provider import get_multi_provider` exists in [ai.py](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py) (line 22) but is never called.

| File | Current Behavior | Target Behavior |
|------|-----------------|-----------------|
| [ai.py](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py) | Hardcodes Mistral HTTP calls for [generate_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#622-855) + [generate_streaming_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#905-1154) | Delegates to `multi_provider.generate()` / `multi_provider.generate_streaming()` |
| [deep_research.py](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py) | [_call_llm()](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py#652-742) tries mistral-large → medium → small via direct HTTP | Delegates to `multi_provider.generate()` with mode `"deep_research"` |
| [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py) | Fully built but unused | No changes needed (already correct) |

## Proposed Changes

### Component 1: Main Chat AI Service

#### [MODIFY] [ai.py](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py)

**1a. Wire [generate_streaming_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#905-1154) (lines 905–1153) to multi_provider**

Replace the current Mistral-only streaming block (lines ~1037–1147) with a call to `multi_provider.generate_streaming()`. The surrounding logic (RAG context, history, tool execution, message building, keep-alive pinger) remains untouched.

```diff
-            # Model selection based on mode
-            if mode == "fast":
-                model_name = "mistral-small-latest"
-            else:
-                model_name = "mistral-large-latest"
-            
-            # ... all the mistral-only HTTP streaming code ...
+            # Delegate to multi-provider routing
+            mp = get_multi_provider()
+            async for token in mp.generate_streaming(
+                messages=messages,
+                mode=mode,
+                max_tokens=max_tokens,
+                temperature=0.7,
+            ):
+                yield token
```

Key decisions:
- The keep-alive pinger is **removed** because `multi_provider.generate_streaming` already handles timeouts and retries internally
- The `mistral_limiter` calls are **removed** because [multi_provider](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#349-354) has its own per-provider RPM tracking
- The [_stream_nvidia_kimi](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#1155-1231) method becomes **dead code** (it's replaced by multi_provider's NVIDIA routing) — mark for removal

**1b. Wire [generate_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#622-855) (lines 622–854) to multi_provider**

Replace the Mistral-only non-streaming block with:

```diff
-            # ... Mistral HTTP call with retry logic ...
+            mp = get_multi_provider()
+            response_text = await mp.generate(
+                messages=messages,
+                mode=mode,
+                max_tokens=max_tokens,
+                temperature=0.7,
+            )
+            return response_text
```

**1c. Keep untouched:**
- [_get_system_prompt()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#399-621) — no changes needed
- [_build_user_message()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#856-894) — no changes needed
- [generate_support_response()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#1387-1458) — intentionally stays Mistral-only (low-volume, specialized prompt)
- [analyze_image()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#1319-1386) / [analyze_image_with_kimi()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#1232-1291) — stays as-is (vision-specific)
- [enhance_image_prompt()](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#160-218) — stays as-is

---

### Component 2: Deep Research Service

#### [MODIFY] [deep_research.py](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py)

**2a. Refactor [_call_llm](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py#652-742) (lines 652–741) to use multi_provider**

```diff
-    async def _call_llm(self, system_prompt, user_prompt, json_mode=False, max_tokens=4000):
-        # ... hardcoded Mistral models_to_try loop ...
+    async def _call_llm(self, system_prompt, user_prompt, json_mode=False, max_tokens=4000):
+        from app.services.multi_provider import get_multi_provider
+        mp = get_multi_provider()
+        messages = [
+            {"role": "system", "content": system_prompt},
+            {"role": "user", "content": user_prompt}
+        ]
+        return await mp.generate(
+            messages=messages,
+            mode="deep_research",
+            max_tokens=max_tokens,
+            temperature=0.3 if json_mode else 0.7,
+        )
```

> [!WARNING]
> The current [_call_llm](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py#652-742) supports `json_mode=True` via `response_format: {"type": "json_object"}`. `multi_provider.generate()` does not currently pass this through. We have two options:
> 1. **Add a `json_mode` parameter to `multi_provider.generate()`** — cleaner but requires modifying multi_provider
> 2. **Post-process the response in [_call_llm](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py#652-742)** — hacky but zero multi_provider changes
>
> **Recommendation:** Option 1 — add `json_mode` param to [generate()](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#298-344) and [generate_streaming()](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#223-297) in multi_provider.py. This is a small, safe change (just add `response_format` to the payload when `json_mode=True`).

---

### Component 3: Multi-Provider Service (Minor Enhancement)

#### [MODIFY] [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py)

**3a. Add `json_mode` support to [generate()](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#298-344)**

```diff
 async def generate(
     self,
     messages,
     mode="detailed",
     max_tokens=4096,
     temperature=0.7,
+    json_mode=False,
 ) -> str:
     # ... existing code ...
     json_payload = {
         "model": model,
         "messages": messages,
         "max_tokens": max_tokens,
         "temperature": temperature,
     }
+    if json_mode:
+        json_payload["response_format"] = {"type": "json_object"}
```

**3b. Update Groq model mapping for Kimi K2**

```diff
 models={
     "fast": "llama-3.1-8b-instant",
     "detailed": "llama-3.3-70b-versatile",
-    "deep_research": "llama-3.3-70b-versatile",
+    "deep_research": "moonshotai/kimi-k2",
 },
```

> [!NOTE]
> Verify `moonshotai/kimi-k2` is available on Groq's free tier before deploying. If not, keep `llama-3.3-70b-versatile` as fallback.

---

### Component 4: Dead Code Cleanup (Post-Integration)

After wiring is confirmed working:

- `AIService._stream_nvidia_kimi()` — now redundant (multi_provider handles NVIDIA streaming)
- `AIService.NVIDIA_BASE_URL` / `AIService.NVIDIA_MODEL` class vars — now redundant
- `mistral_limiter` usage in [generate_streaming_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#905-1154) and [generate_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#622-855) — now redundant (multi_provider has its own RPM tracking)

These should be **identified but not removed** until the integration is verified.

---

## Verification Plan

### Automated Tests

**Existing test suite** (2,997 lines of property-based tests):

```bash
cd /Users/mac/Desktop/phhh/backend
python -m pytest tests/test_multi_provider_properties.py -v --tb=short
```

This validates:
- Provider initialization (all 3 providers created with correct models/weights/RPM)
- Mode-to-model mapping correctness
- Priority routing order per mode
- Rate limit detection and marking (429 → exhausted)
- Cooldown periods (60s RPM, 24h daily)
- Weighted fallback selection
- Health-aware provider selection

> [!IMPORTANT]
> These tests mock `settings` so they don't require real API keys. They should pass as-is since we're not changing [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py) logic (only adding `json_mode` param).

### Manual Verification

1. **Set all 3 API keys** in [backend/.env](file:///Users/mac/Desktop/phhh/backend/.env):
   ```
   MISTRAL_API_KEY=...
   GROQ_API_KEY=...
   NVIDIA_API_KEY=...
   ```

2. **Start the backend:**
   ```bash
   cd /Users/mac/Desktop/phhh/backend
   python -m uvicorn main:app --reload --port 8000
   ```

3. **Verify provider initialization** — look for these log lines on startup:
   ```
   ✅ NVIDIA NIM provider initialized (Primary - 80% weight)
   ✅ Groq provider initialized (Fast mode - 15% weight)
   ✅ Mistral provider initialized (Fallback - 5% weight)
   🔄 Multi-provider routing enabled: ['nvidia', 'groq', 'mistral']
   ```

4. **Send test requests** via the frontend or curl, using each mode (`fast`, `detailed`, `deep_research`). Confirm the logs show the correct primary provider being selected:
   - `fast` → should show `✅ Selected groq with model llama-3.1-8b-instant`
   - `detailed` → should show `✅ Selected nvidia with model qwen/qwen3.5-397b-a17b`
   - `deep_research` → should show `✅ Selected nvidia with model qwen/qwen3.5-397b-a17b`

5. **Verify failover** — temporarily set an invalid NVIDIA API key, send a `detailed` request, and confirm it silently falls back to Groq or Mistral without the user seeing an error.
