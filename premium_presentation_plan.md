# Benchside Premium Presentation Platform - Implementation Plan

## Overview
Transform Benchside from a standard AI generator to a premium presentation platform through three strategic phases.

---

## Phase 1: Prompt Engineering & Content Diet (IMMEDIATE - Week 1)

### 1.1 Global Art Direction Wrapper
**File:** `backend/app/services/slide_service.py`

**Problem:** Visual whiplash - inconsistent styles from comic to 3D renders

**Solution:** Intercept image_prompt before Pollinations API and wrap with strict style definition

**Implementation:**
```python
ART_DIRECTION_STYLES = {
    "corporate": "Professional corporate vector illustration, minimalist, flat design, white background, unified color palette. No text.",
    "photorealistic": "High-quality photorealistic render, professional lighting, clean composition, corporate setting. No text.",
    "minimalist": "Ultra-minimalist line art, monochrome, geometric shapes, ample white space. No text.",
    "isometric": "Isometric 3D illustration, soft shadows, pastel colors, clean modern style. No text."
}

def wrap_image_prompt(base_prompt: str, style: str = "corporate") -> str:
    style_prompt = ART_DIRECTION_STYLES.get(style, ART_DIRECTION_STYLES["corporate"])
    return f"{base_prompt}. {style_prompt}"
```

### 1.2 Contextual Memory (Prevent Repetition)
**File:** `backend/app/services/slide_service.py` - `_refine_slide_content()`

**Problem:** AI repeats phrases like "AI accelerates drug discovery" across slides

**Solution:** Pass slide context between iterations

**Implementation:**
- Add `previous_slides_summary` parameter to refinement function
- Store key phrases/concepts from previous slides
- Include in prompt: "Avoid repeating these concepts: [list]"
- Track unique value propositions per deck

### 1.3 Rule of Three
**File:** `backend/app/services/slide_service.py` - NVIDIA refinement prompt

**Problem:** Slides have too much text (e.g., Thank You slide with 7 bullet points)

**Solution:** Strict content limits in prompts

**Implementation:**
```python
CONTENT_CONSTRAINTS = """
STRICT LIMITS:
- Maximum 3 bullet points per slide
- Maximum 12 words per bullet point
- Maximum 1 sentence per bullet point
- No paragraph text
- Focus on single concept per slide
"""
```

### 1.4 Named Entities Requirement
**File:** `backend/app/services/slide_service.py` - Groq outline generation

**Problem:** Content is too generic

**Solution:** Force specific examples, case studies, real companies

**Implementation:**
Add to initial outline prompt:
```
For each slide requiring examples, you MUST include:
- At least 1 specific company name (e.g., "Pfizer", "DeepMind")
- At least 1 specific AI model or technology (e.g., "AlphaFold", "GPT-4")
- At least 1 real-world metric or statistic with source
- At least 1 named case study or clinical trial

Do not use generic phrases like "many companies" or "various AI tools".
```

---

## Phase 2: Backend Architecture (MEDIUM TERM - Weeks 2-3)

### 2.1 Smart Layout Mapping
**File:** `backend/app/services/slide_service.py`

**Problem:** Generic bullet lists for all content types

**Solution:** Content type detection → Layout mapping

**Content Types:**
```python
LAYOUT_MAPPINGS = {
    "chronological": "timeline",      # Process/steps
    "comparison": "two_column",       # Pros/cons, vs
    "data_heavy": "chart",            # Statistics, metrics
    "hierarchical": "pyramid",        # Org structure, levels
    "problem_solution": "split",      # Challenge → Answer
    "single_concept": "hero",         # Focus slide
    "list": "bullet_grid"             # Multiple items
}
```

**Implementation:**
- Add content classification step in slide generation
- Pass layout_type to DesignEngine
- DesignEngine selects template based on type

### 2.2 Native Data Visualizations
**File:** `backend/app/services/slide_service.py` + `backend/app/services/design_engine.py`

**Problem:** Numbers like "85%" are just text callouts

**Solution:** Generate native charts with python-pptx

**JSON Schema Update:**
```json
{
  "chart_data": {
    "type": "bar|pie|line",
    "title": "Chart Title",
    "labels": ["Q1", "Q2", "Q3"],
    "values": [85, 92, 78],
    "colors": ["#4472C4", "#ED7D31", "#A5A5A5"]
  }
}
```

**Implementation:**
```python
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE

def add_chart_to_slide(slide, chart_data):
    chart_data_obj = ChartData()
    chart_data_obj.categories = chart_data['labels']
    chart_data_obj.add_series('Series 1', chart_data['values'])
    
    x, y, cx, cy = Inches(1), Inches(2), Inches(8), Inches(4.5)
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data_obj
    ).chart
```

### 2.3 Fix Reference Hallucinations
**Files:** `backend/app/services/slide_service.py`

**Problem:** References slide lists generic claims, not real sources

**Solution A:** Use literature search to pull real citations
- Integrate with existing PubMed/Semantic Scholar search
- Extract APA-formatted citations
- Verify sources exist

**Solution B:** Drop references slide if no verified sources
- Check if citations are real URLs or just text
- If < 3 verified sources, skip references slide
- Add "Sources available upon request" disclaimer

---

## Phase 3: Killer UX Enhancements (LONG TERM - Weeks 4-6)

### 3.1 Granular Asset Regeneration
**Files:** 
- `frontend/src/components/studio/CreationStudio.tsx`
- New: `frontend/src/components/studio/SlidePreview.tsx`

**Problem:** Users must regenerate entire deck to fix one slide

**Solution:** Visual preview + per-slide actions

**Implementation:**
1. Add preview step before download (grid of slide thumbnails)
2. Click slide to expand:
   - "Regenerate Image" button → call image_gen_service
   - "Rewrite Text" button → call refinement with new prompt
   - Manual text editing textarea
3. Store editable JSON state in frontend
4. Allow selective regeneration (only changed slides)

**UI Flow:**
```
Outline → Generate → Preview Grid → [Edit Individual Slides] → Download
```

### 3.2 Vibe Selection
**File:** `frontend/src/components/studio/CreationStudio.tsx`

**Problem:** No control over visual style

**Solution:** Style selector in creation form

**Implementation:**
```typescript
const VIBE_OPTIONS = [
  { id: "corporate", label: "Corporate Vector", icon: Building },
  { id: "photorealistic", label: "Photorealistic", icon: Camera },
  { id: "minimalist", label: "Minimalist", icon: Minimize2 },
  { id: "isometric", label: "Isometric 3D", icon: Box },
  { id: "sketch", label: "Hand Sketch", icon: Pencil }
];
```

- Pass selected vibe to backend via API
- Store in slide generation context
- Apply to all image prompts via Art Direction Wrapper

### 3.3 Clean Closing Slides
**File:** `backend/app/services/design_engine.py`

**Problem:** Thank You slide has content summaries

**Solution:** Hardcoded logic for closing slides

**Implementation:**
```python
CLOSING_SLIDE_RULES = {
    "title_slide": {
        "max_elements": 2,  # Title + subtitle only
        "allowed_types": ["title", "subtitle"],
        "forbidden": ["bullets", "images", "charts"]
    },
    "thank_you_slide": {
        "max_elements": 3,  # Title + contact + optional logo
        "allowed_types": ["title", "text", "image"],
        "forbidden": ["bullets", "charts", "summaries"],
        "required_text": "Thank You"
    }
}
```

**Enforcement:**
- Detect slide type by position (first/last) or content
- Apply strict rules
- Override AI-generated content if it violates rules
- Force minimal, clean design

---

## Implementation Priority

### Week 1 (Phase 1 - Immediate)
- [ ] 1.1 Global Art Direction Wrapper
- [ ] 1.2 Contextual Memory
- [ ] 1.3 Rule of Three
- [ ] 1.4 Named Entities

### Week 2-3 (Phase 2 - Architecture)
- [ ] 2.1 Smart Layout Mapping
- [ ] 2.2 Native Data Visualizations
- [ ] 2.3 Fix References

### Week 4-6 (Phase 3 - UX)
- [ ] 3.1 Granular Asset Regeneration
- [ ] 3.2 Vibe Selection
- [ ] 3.3 Clean Closing Slides

---

## Success Metrics

- **Visual Consistency:** 90%+ of images use unified style
- **Content Quality:** < 5% repetition across slides
- **Engagement:** Users regenerate < 20% of slides (vs 100% now)
- **Professionalism:** 0 closing slides with bullet point summaries
- **Performance:** < 5s per-slide regeneration for edits

---

## Technical Notes

### Dependencies
- `python-pptx` (already installed)
- No new frontend dependencies needed

### API Changes
- POST `/api/v1/slides/generate` - Add `vibe` parameter
- POST `/api/v1/slides/regenerate` - New endpoint for single slide
- GET `/api/v1/slides/preview/{job_id}` - New endpoint for preview

### Database Changes
- None required (stateless generation)

### Breaking Changes
- None (all additions/enhancements)
