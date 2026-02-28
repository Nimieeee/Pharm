# Multi-Provider AI Routing — Implementation Tasks

## Phase 1: Wire [MultiProviderService](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#46-344) into [ai.py](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py) Streaming
- [x] Replace Mistral-only streaming in [generate_streaming_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#905-1154) with `multi_provider.generate_streaming`
- [x] Replace Mistral-only non-streaming in [generate_response](file:///Users/mac/Desktop/phhh/backend/app/services/ai.py#622-855) with `multi_provider.generate`
- [x] Update model selection block (lines ~1037-1046) to delegate to multi_provider routing
- [x] Remove or bypass the `mistral_limiter` calls in favor of per-provider rate tracking
- [x] Keep the keep-alive pinger + queue pattern but source tokens from [multi_provider](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#349-354)

## Phase 2: Wire [MultiProviderService](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py#46-344) into [deep_research.py](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py)
- [x] Refactor [_call_llm](file:///Users/mac/Desktop/phhh/backend/app/services/deep_research.py#652-742) to use `multi_provider.generate()` instead of direct Mistral HTTP calls
- [x] Remove hardcoded `models_to_try` list (mistral-large → medium → small) in favor of mode-based routing

## Phase 3: Update Multi-Provider Enhancements
- [x] Add `json_mode` support to `multi_provider.generate()`
- [ ] Verify NVIDIA `qwen/qwen3.5-397b-a17b` is correct for detailed + research modes

## Phase 4: Prompt Optimization per Provider
- [ ] Audit system prompts for provider-specific quirks (Llama 3 vs Qwen vs Mistral)
- [ ] Add provider name to streaming metadata so frontend can optionally show which model responded

## Phase 5: Verification
- [ ] Run existing property-based tests: `pytest tests/test_multi_provider_properties.py -v`
- [ ] Manual end-to-end test: send fast/detailed/research mode chats and confirm provider rotation
- [ ] Verify 429 failover: artificially exhaust one provider and confirm silent fallback
