# Deep Research Quality Diagnostic: "Gold Standard" vs. "Bloat"

## 1. Executive Summary of Discrepancies
Current production outputs for Deep Research (e.g., `latest_deep_research_report.md`) have diverged significantly from the "Gold Standard" (`final_deep_research_report.md`). 

| Feature | Gold Standard | Current Output (Bloated) |
| :--- | :--- | :--- |
| **Total Length** | ~135 lines (~900 words) | **~450 lines (~3000 words)** |
| **Density** | High (Fact-dense, concise) | **Low (Repetitive prose, filler)** |
| **Structure** | Tight executive flow | **Expanded "Academic" sections** |
| **Logic** | Synthesized findings | **Section-by-section expansion** |
| **Tone** | Expert summary | **Repetitive "Deeply researched" prose** |

---

## 2. Root Cause 1: The "2,500 Word" Requirement
The primary cause of the quality drop is the **System Prompt** in `backend/app/services/deep_research.py`.

```python
# Location: deep_research.py (Line 1215)
report_sys_prompt = f"""You are a senior medical/scientific research analyst.
Your task is to write a comprehensive, highly academic review article (target length: 2,500 words).
"""
```

### The Problem:
- **Artificial Expansion**: LLMs like Gemini-Flash and Kimi-K2 (the current providers) will force-expand sections to hit the 2,500-word target even if the research data is shallow.
- **Narrative Loops**: To hit the word count, the models repeat introductory phrases and generic regulatory context across multiple headers (e.g., repeating the "FDA vs EMA" context in Background, Clinical, and Regulatory sections).

---

## 3. Root Cause 2: Tier 2 Fallback Loop
The backend uses a "Tiered" reporting approach that guarantees degradation on failure.

```python
# Location: deep_research.py (Line 1263-1300)
try:
    # Tier 1: 50 sources, Pollinations (Gemini Fast)
    full_report_content = await self._call_llm(..., mode="deep_research_elite", ...)
except Exception:
    # Tier 2: 20 sources, Groq (Kimi K2)
    used_citations = sorted_citations[:20]
    full_report_content = await self._call_llm(..., mode="deep_research_single_pass", ...)
```

### The Problem:
- **Source Starvation**: If Tier 1 fails (common due to Pollinations reliability), Tier 2 attempts to write the *same* 2,500-word exhaustive report using only **20 sources** instead of 50.
- **Result**: The LLM has 60% less data but is forced to write a report of the same length, leading to a massive increase in "filler" content and repetition.

---

## 4. Root Cause 3: Benchmark "Overfitting"
The prompt (Line 1219) demands 6 "Gold Standard Benchmarks":
1. Quantitative Density
2. Structural Landscape Tables
3. Trial Identity Binding
4. Molecular Granularity
5. Evidence Gap Analysis
6. Triple-Cite Core Claims

### The Problem:
- **Low-Reliability Data**: Web search results (Tavily/DDG) often don't contain the raw IC50 values or NCT IDs needed to satisfy Benchmark #1 and #3.
- **Failure Mode**: Instead of admitting the data is missing, the LLM hallucinates "academic-sounding" proxies or repeats generic sentences many times to "look" like a high-impact journal article.

---

## 5. Root Cause 4: Persistence Bug (State Leak)
The user reported the "Issue still persisting" regarding the empty reports.

### Code Analysis:
The `asyncio.wait_for` fix **IS present** in `backend/app/api/v1/endpoints/ai.py` (Line 1169):
```python
# Using non-destructive heartbeat
research_gen = research_service.run_research_streaming(...)
# ...
done, pending = await asyncio.wait(
    {next_task, sleep_task},
    return_when=asyncio.FIRST_COMPLETED
)
```
### Why it might still fail:
1. **Model Timeout**: The LLM call in `_call_llm` uses a 600s timeout (in `multi_provider.py`), but if the connection is slow, the SSE stream from the provider might hang without yielding, causing the `generate_stream` to stall.
2. **Memory/Token Limit**: `max_tokens=25000` is requested in `deep_research.py:1267`. Many providers (Pollinations/Groq) have hard limits much lower than this (e.g., 8192 or 16384), causing silent truncation or error fallbacks mid-generation.

---

## 6. Recommended Fixes

### [FIX A] Prompt Tightening
- **Reduce** target length from 2,500 words → 1,200 words (matching the Gold Standard).
- **Add** a "Concistency over Length" instruction: *"If data is unavailable for a benchmark, DO NOT use filler text. Keep it concise."*

### [FIX B] Adaptive Tiering
- If falling back to Tier 2 (20 sources), the prompt should **explicitly reduce target length** to 800 words to maintain density.

### [FIX C] Title Cleanup
- Hardcode the `# {state.research_question}` format to prevent the LLM from adding the characteristic `# deeply Researched Report:` prefix.

### [FIX D] Token Safety
- Reduce `max_tokens` from 25,000 to 8,000 to stay within provider safe zones and prevent mid-writing timeouts.
