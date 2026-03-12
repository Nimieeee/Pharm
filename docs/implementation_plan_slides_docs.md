# Kimi-Style Slide & Document Generator — Complete Implementation Plan

> **Version**: 1.0 · March 2026
> **Scope**: Agentic slide + document generation with design intelligence, Pollinations image gen, and professional export
> **Estimated Effort**: ~55-65 hours across 3 phases
> **Also in**: `docs/implementation_plan_slides_docs.md` (this file)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Existing Infrastructure](#2-existing-infrastructure)
3. [Phase A: Slide Generator Core](#3-phase-a-slide-generator-core-25-hrs)
4. [Phase B: Pollinations Image Generation](#4-phase-b-pollinations-image-generation-12-hrs)
5. [Phase C: Document Generator](#5-phase-c-document-generator-18-hrs)
6. [Design Intelligence Engine](#6-design-intelligence-engine)
7. [Anti-Regression Strategy](#7-anti-regression-strategy)
8. [Verification Plan](#8-verification-plan)

---

## 1. Executive Summary

Build a 4-step agentic pipeline that converts a topic, URL, or uploaded document into professional slides or structured documents:

```
Input (topic / URL / file)
  → Step 1: AI generates editable outline (JSON)
  → Step 2: User edits outline in visual editor
  → Step 3: AI generates content + Pollinations images
  → Step 4: Design Engine assembles PPTX/DOCX with professional theming
  → Output: downloadable .pptx or .docx
```

---

## 2. Existing Infrastructure

Everything we build on already exists and is production-tested.

| Component | File | What It Does | How We Use It |
|-----------|------|-------------|---------------|
| **Image Generation** | `backend/app/services/image_gen.py` (109 lines) | `fetch_image_from_pollinations()` returns raw PNG bytes. 5,000/day with API key. Supports FLUX Schnell + Imagen-4 | Generate one image per slide |
| **Multi-Provider AI** | `backend/app/services/multi_provider.py` (464 lines) | 4 providers, 5 modes, health-aware failover | Groq fast for outlines, NVIDIA detailed for slide prose |
| **DOCX Export** | `backend/app/api/v1/endpoints/export.py` (303 lines) | python-docx DOCX + xhtml2pdf PDF with Kroki mermaid rendering | Extend for structured documents |
| **Deep Research UI** | `frontend/src/components/chat/DeepResearchUI.tsx` (418 lines) | SSE progress bar, left/right panel layout, animated loading | Clone pattern for slide progress UI |
| **Chat Modes** | `frontend/src/components/chat/ChatInput.tsx` (789 lines) | 3 modes: fast/detailed/deep_research | Detect slide/doc intent from message |
| **Glass Cards** | `frontend/src/components/ui/GlassCard.tsx` (2KB) | Glassmorphism card component | Use in outline editor |
| **Framer Motion** | Already in `package.json` | Animations for drag-drop, transitions | Outline editor interactions |
| **Lucide Icons** | Already in `package.json` | Icon library | Design system icons |
| **Sonner** | Already in `package.json` | Toast notifications | Generation progress toasts |

---

## 3. Phase A: Slide Generator Core (~25 hrs)

### 3.1 Backend: SlideService

#### [NEW] `backend/app/services/slide_service.py` (~500 lines)

This is the core backend service. It orchestrates the 4-step pipeline.

```python
"""
Slide Generation Service — Kimi-style agentic pipeline.

Step 1: generate_outline()  — AI creates JSON slide structure
Step 2: refine_content()    — AI writes full prose per slide
Step 3: generate_images()   — Pollinations creates visuals
Step 4: assemble_pptx()     — Design Engine builds the file
"""

import json
import asyncio
from typing import Optional, Callable
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from app.services.multi_provider import MultiProviderService
from app.services.image_gen import ImageGenerationService

class SlideService:
    def __init__(self, multi_provider: MultiProviderService, 
                 image_gen: ImageGenerationService):
        self.ai = multi_provider
        self.image_gen = image_gen
        self.design = DesignEngine()  # See Section 6
    
    async def generate_outline(
        self, 
        topic: str, 
        context: str = None,
        num_slides: int = 12,
        uploaded_text: str = None  # From RAG-ingested document
    ) -> dict:
        """
        Step 1: AI generates editable JSON outline.
        
        Uses Groq fast mode for speed (~2-3 seconds).
        If uploaded_text is provided, the AI distills it into slides.
        """
        source_context = ""
        if uploaded_text:
            # Truncate to 8000 chars for fast mode token limit
            source_context = f"\n\nSource material to distill:\n{uploaded_text[:8000]}"
        elif context:
            source_context = f"\n\nAdditional context:\n{context}"
        
        prompt = f"""Create a presentation outline on: "{topic}"
Number of slides: {num_slides}
{source_context}

Return ONLY valid JSON with this exact schema:
{{
  "title": "Presentation Title",
  "subtitle": "Subtitle",
  "theme": "ocean_gradient",
  "slides": [
    {{
      "slide_number": 1,
      "layout": "title",
      "title": "Slide Title",
      "subtitle": "Optional subtitle",
      "bullets": ["Point 1", "Point 2"],
      "speaker_notes": "What to say...",
      "image_prompt": "description of image to generate, or null for no image",
      "data": null
    }}
  ]
}}

Layout options: "title", "two_column", "bullets_only", "data_callout", "image_full"
Theme options: "ocean_gradient", "forest_moss", "coral_energy", "warm_terracotta", 
               "charcoal_minimal", "teal_trust", "berry_cream", "sage_calm", 
               "cherry_bold", "midnight_executive"

Rules:
- First slide MUST be layout "title"
- Last slide should be "title" (conclusion/thank you)
- Never have 3 consecutive slides with the same layout
- Max 6 bullets per slide (split if more needed)
- image_prompt should describe a professional, relevant illustration
- For data_callout: include "data": {{"value": "85%", "label": "Patient Response Rate"}}
"""
        
        response = await self.ai.chat_completion(
            mode="fast",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3
        )
        
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        
        outline = json.loads(json_str)
        
        # Apply design intelligence adjustments
        outline = self.design.analyze_and_adjust(outline)
        
        return outline
    
    async def generate_slides(
        self,
        outline: dict,
        generate_images: bool = True,
        on_progress: Optional[Callable] = None
    ) -> bytes:
        """
        Steps 2-4: Generate content, images, assemble PPTX.
        
        Reports progress via on_progress callback (for SSE).
        Returns PPTX file as bytes.
        """
        total_slides = len(outline["slides"])
        theme = self.design.get_theme(outline.get("theme", "ocean_gradient"))
        content_results = []
        image_results = {}
        
        # Step 2: Generate full content per slide (parallel where possible)
        for i, slide in enumerate(outline["slides"]):
            if on_progress:
                await on_progress({
                    "step": "content",
                    "current": i + 1,
                    "total": total_slides,
                    "message": f"Writing slide {i+1}: {slide['title']}"
                })
            
            # Refine bullet points into fuller content
            refined = await self._refine_slide_content(slide, outline["title"])
            content_results.append(refined)
        
        # Step 3: Generate images via Pollinations
        if generate_images:
            image_tasks = []
            for i, slide in enumerate(outline["slides"]):
                if slide.get("image_prompt"):
                    image_tasks.append((i, slide["image_prompt"]))
            
            for idx, (slide_idx, prompt) in enumerate(image_tasks):
                if on_progress:
                    await on_progress({
                        "step": "images",
                        "current": idx + 1,
                        "total": len(image_tasks),
                        "message": f"Generating image {idx+1}/{len(image_tasks)}"
                    })
                
                try:
                    img_bytes = await self.image_gen.fetch_image_from_pollinations(
                        prompt=prompt,
                        model="flux",
                        width=1024,
                        height=768,
                        seed=42 + slide_idx
                    )
                    image_results[slide_idx] = img_bytes
                except Exception as e:
                    # Image failure is non-fatal — slide works without image
                    image_results[slide_idx] = None
        
        # Step 4: Assemble PPTX with Design Engine
        if on_progress:
            await on_progress({
                "step": "assembly",
                "current": total_slides,
                "total": total_slides,
                "message": "Assembling presentation..."
            })
        
        pptx_bytes = self.design.assemble_pptx(
            outline=outline,
            content=content_results,
            images=image_results,
            theme=theme
        )
        
        if on_progress:
            await on_progress({
                "step": "complete",
                "current": total_slides,
                "total": total_slides,
                "message": "Presentation ready!"
            })
        
        return pptx_bytes
    
    async def _refine_slide_content(self, slide: dict, deck_title: str) -> dict:
        """Use detailed AI to expand bullet points into polished content"""
        if slide["layout"] == "title":
            return slide  # Title slides don't need expansion
        
        prompt = f"""Refine this slide content for the presentation "{deck_title}".

Slide title: {slide['title']}
Bullets: {json.dumps(slide.get('bullets', []))}

Rules:
- Keep each bullet under 15 words
- Make language active and concrete
- Add a 2-sentence speaker note
- Return as JSON: {{"bullets": [...], "speaker_notes": "..."}}"""
        
        response = await self.ai.chat_completion(
            mode="detailed",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4
        )
        
        try:
            refined = json.loads(response.strip().replace("```json", "").replace("```", ""))
            slide["bullets"] = refined.get("bullets", slide.get("bullets", []))
            slide["speaker_notes"] = refined.get("speaker_notes", slide.get("speaker_notes", ""))
        except json.JSONDecodeError:
            pass  # Keep original content if parsing fails
        
        return slide
```

**Where**: `backend/app/services/slide_service.py`
**Dependencies**: `python-pptx` (pip install), existing `multi_provider.py`, existing `image_gen.py`

---

### 3.2 Backend: API Endpoints

#### [NEW] `backend/app/api/v1/endpoints/slides.py` (~200 lines)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio, json, io, uuid

router = APIRouter()

# --- Request/Response Models ---

class SlideOutlineRequest(BaseModel):
    topic: str
    num_slides: int = 12
    context: Optional[str] = None
    conversation_id: Optional[str] = None  # To pull RAG context

class SlideOutline(BaseModel):
    title: str
    subtitle: Optional[str] = None
    theme: str = "ocean_gradient"
    slides: List[dict]

class SlideGenerateRequest(BaseModel):
    outline: SlideOutline
    generate_images: bool = True

# --- Storage for in-progress jobs ---
slide_jobs: dict = {}  # job_id -> {"status": ..., "pptx_bytes": ...}

# --- Endpoints ---

@router.post("/slides/outline")
async def generate_slide_outline(
    request: SlideOutlineRequest,
    current_user = Depends(get_current_user),
    slide_service = Depends(get_slide_service)
):
    """Step 1: Generate editable JSON outline from topic"""
    context = None
    if request.conversation_id:
        # Pull existing conversation context via RAG
        context = await get_conversation_context(request.conversation_id)
    
    outline = await slide_service.generate_outline(
        topic=request.topic,
        context=context or request.context,
        num_slides=request.num_slides
    )
    return outline

@router.post("/slides/generate")
async def generate_slides(
    request: SlideGenerateRequest,
    current_user = Depends(get_current_user),
    slide_service = Depends(get_slide_service)
):
    """Step 2-4: Generate PPTX from approved outline. Returns SSE progress."""
    job_id = str(uuid.uuid4())
    slide_jobs[job_id] = {"status": "started", "pptx_bytes": None}
    
    async def event_generator():
        async def on_progress(data):
            yield {"event": "progress", "data": json.dumps(data)}
        
        try:
            pptx_bytes = await slide_service.generate_slides(
                outline=request.outline.dict(),
                generate_images=request.generate_images,
                on_progress=on_progress
            )
            slide_jobs[job_id]["pptx_bytes"] = pptx_bytes
            slide_jobs[job_id]["status"] = "complete"
            yield {"event": "complete", "data": json.dumps({"job_id": job_id})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
    
    return EventSourceResponse(event_generator())

@router.get("/slides/download/{job_id}")
async def download_slides(job_id: str, current_user = Depends(get_current_user)):
    """Download generated PPTX"""
    job = slide_jobs.get(job_id)
    if not job or not job["pptx_bytes"]:
        raise HTTPException(404, "Slide job not found or not complete")
    
    return StreamingResponse(
        io.BytesIO(job["pptx_bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=benchside_slides_{job_id[:8]}.pptx"}
    )
```

**Where**: `backend/app/api/v1/endpoints/slides.py`
**Register in**: `backend/app/api/v1/router.py` — add `router.include_router(slides.router, prefix="/slides", tags=["slides"])`

---

### 3.3 Frontend: Slide Generation UI

The UI has **3 states**, modeled after `DeepResearchUI.tsx`:

#### State 1: Outline Editor (after outline is generated)

#### [NEW] `frontend/src/components/slides/SlideOutlineEditor.tsx` (~400 lines)

**What it looks like**:
- Full-width card replacing the chat response area (same pattern as `DeepResearchUI.tsx`)
- **Header bar**: Presentation title (editable), theme selector dropdown, "Generate Slides" button
- **Left panel (70%)**: Slide list as draggable cards
  - Each card shows: slide number, title (editable), layout badge, bullet count
  - Expand/collapse to show bullets and speaker notes (both editable)
  - Drag handle on left edge for reordering (use `@dnd-kit/core` or framer-motion `Reorder`)
  - "Add Slide" button at bottom, "Delete" icon on each card
  - Image toggle (checkbox: "Generate image for this slide")
- **Right panel (30%)**: Theme preview
  - Shows 2-3 preview thumbnails with the selected theme colors
  - Theme name + color swatches
  - Theme dropdown: 10 options, each showing 3 color dots

**Technology**: React + framer-motion + lucide-react (consistent with existing stack)

```tsx
// Key props interface
interface SlideOutlineEditorProps {
  outline: SlideOutline;                    // From POST /slides/outline
  onOutlineChange: (outline: SlideOutline) => void;  // For local edits
  onGenerate: (outline: SlideOutline) => void;       // Trigger generation
  onCancel: () => void;
}
```

**UI behavior**:
- Slide cards use `GlassCard.tsx` wrapper for glassmorphism look
- Drag-drop uses `framer-motion`'s `Reorder.Group` + `Reorder.Item`
- Theme selector uses `AnimatePresence` for smooth transition
- Real-time validation: red badge if any slide has >6 bullets or >80 words
- "Add Slide" inserts after currently selected slide

#### State 2: Generation Progress

#### [NEW] `frontend/src/components/slides/SlideProgress.tsx` (~200 lines)

**What it looks like** (directly mirrors `DeepResearchUI.tsx` loading state):
- Centered animated Benchside logo with spinner ring (reuse `StreamingLogo.tsx`)
- Progress text: "Writing slide 4/12: Mechanism of Action..."
- Progress bar: gradient amber→orange (same as deep research)
- Below progress bar: 3 phase indicators:
  - ✅ Content (when content step done)
  - 🔄 Images (when generating images)
  - ⏳ Assembly (waiting)
- When complete: "Presentation Ready!" with animated download button

```tsx
interface SlideProgressProps {
  currentStep: "content" | "images" | "assembly" | "complete";
  currentSlide: number;
  totalSlides: number;
  totalImages: number;
  message: string;
  onDownload?: () => void;  // Active when complete
}
```

#### State 3: Trigger Detection (in ChatInput)

#### [MODIFY] `frontend/src/components/chat/ChatInput.tsx`

**How the user triggers slide generation**:

Instead of adding a 4th mode button, we use **intent detection** in the chat input:

```tsx
// Add to ChatInput.tsx — detect slide/doc intent from message
const SLIDE_TRIGGERS = [
  "create a presentation", "make slides", "generate slides", 
  "slide deck", "pptx", "powerpoint", "create a deck",
  "make a presentation", "presentation about", "presentation on"
];

const DOC_TRIGGERS = [
  "write a report", "generate a document", "create a whitepaper",
  "write a manuscript", "structured document", "create a report"
];

function detectIntent(message: string): "slides" | "document" | "chat" {
  const lower = message.toLowerCase();
  if (SLIDE_TRIGGERS.some(t => lower.includes(t))) return "slides";
  if (DOC_TRIGGERS.some(t => lower.includes(t))) return "document";
  return "chat";
}
```

When intent is "slides" or "document", the `onSend` handler invokes the outline API instead of the normal chat API. The response replaces the chat message area with `SlideOutlineEditor` or `DocOutlineEditor`.

**Alternatively**, add a small icon button next to the send button:
- 📊 (Presentation) icon — opens a focused slide creation dialog
- 📝 (Document) icon — opens a focused document creation dialog
- These appear as a small toolbar row above the input area

**Where these live in the frontend**:

```
frontend/src/components/
├── slides/                      # [NEW] Slide generation directory
│   ├── SlideOutlineEditor.tsx   # Outline editor with drag-drop
│   ├── SlideProgress.tsx        # SSE progress display
│   └── ThemeSelector.tsx        # Theme preview/picker
├── docs/                        # [NEW] Document generation directory
│   ├── DocOutlineEditor.tsx     # Document section editor
│   └── DocProgress.tsx          # Generation progress
├── chat/
│   ├── ChatInput.tsx            # [MODIFY] Add intent detection + trigger icons
│   ├── ChatMessage.tsx          # [MODIFY] Render SlideOutlineEditor in message
│   └── DeepResearchUI.tsx       # [REFERENCE] Pattern to follow
└── ui/
    └── GlassCard.tsx            # [REUSE] For outline cards
```

---

### 3.4 Backend: Router Registration

#### [MODIFY] `backend/app/api/v1/router.py`

```python
# Add after existing router includes:
from app.api.v1.endpoints.slides import router as slides_router
router.include_router(slides_router, prefix="/slides", tags=["slides"])
```

---

## 4. Phase B: Pollinations Image Generation (~12 hrs)

### 4.1 Per-Slide Image Generation

#### [MODIFY] `backend/app/services/image_gen.py`

Add a slide-specific method:

```python
async def generate_slide_image(self, prompt: str, slide_number: int) -> bytes:
    """Generate a slide-quality image via Pollinations.
    
    Uses larger resolution (1024x768) and slide-appropriate styling.
    Returns raw PNG bytes for embedding in PPTX.
    """
    # Add slide-specific style keywords
    style = "clean professional illustration, high resolution, modern design, flat design style, white or clean background, suitable for presentation slide"
    full_prompt = f"{prompt}, {style}"
    
    return await self.fetch_image_from_pollinations(
        prompt=full_prompt,
        model="flux",
        width=1024,
        height=768,
        seed=42 + slide_number  # Reproducible per slide
    )
```

**Where**: Add to existing `backend/app/services/image_gen.py`

**UI impact**: When images are being generated, `SlideProgress.tsx` shows:
- "Generating image 3/8: Kidney nephron diagram..."
- Each completed image shows as a small thumbnail in the progress panel

### 4.2 Image Fallback Strategy

If Pollinations fails for a slide (timeout, rate limit):
1. Retry once with simplified prompt (first 50 chars)
2. If still fails: skip image for that slide (layout auto-adjusts to `bullets_only`)
3. Never block the entire deck because one image failed
4. Log failure for monitoring

---

## 5. Phase C: Document Generator (~18 hrs)

### 5.1 Backend: DocService

#### [NEW] `backend/app/services/doc_service.py` (~400 lines)

```python
class DocService:
    """Structured document generation with outline-first workflow"""
    
    DOC_TYPES = {
        "report": {
            "sections": ["Executive Summary", "Introduction", "Methodology",
                         "Findings", "Discussion", "Conclusion", "References"],
            "citation_style": "apa"
        },
        "manuscript": {
            "sections": ["Abstract", "Introduction", "Methods", "Results",
                         "Discussion", "Conclusion", "References"],
            "citation_style": "vancouver"
        },
        "whitepaper": {
            "sections": ["Executive Summary", "Problem Statement", 
                         "Proposed Solution", "Technical Details", 
                         "Case Studies", "Implementation", "Conclusion"],
            "citation_style": "apa"
        },
        "case_report": {
            "sections": ["Abstract", "Introduction", "Case Presentation",
                         "Investigations", "Treatment", "Outcome", 
                         "Discussion", "References"],
            "citation_style": "vancouver"
        }
    }
    
    async def generate_outline(self, topic: str, doc_type: str = "report",
                                context: str = None) -> dict:
        """Generate editable document outline"""
        # AI generates section structure with key points per section
        # Returns JSON: {title, doc_type, sections: [{heading, subheadings, key_points}]}
    
    async def generate_document(self, outline: dict,
                                 on_progress = None) -> bytes:
        """Generate full DOCX from approved outline"""
        # For each section:
        #   1. AI generates full prose (NOT bullets — paragraph format)
        #   2. Extract DOIs/PMIDs → resolve citations via CrossRef (if WS4 exists)
        #   3. Generate figures if needed via Pollinations
        # Assemble with python-docx:
        #   - Title page with Benchside branding
        #   - Table of Contents
        #   - Numbered section headings
        #   - Page numbers in footer
        #   - "Generated by Benchside" watermark footer
        #   - References section at end
```

**Where**: `backend/app/services/doc_service.py`

### 5.2 Frontend: DocOutlineEditor

#### [NEW] `frontend/src/components/docs/DocOutlineEditor.tsx` (~350 lines)

**What it looks like**:
- Sidebar-free layout (docs need more width than slides)
- **Header**: Document title (editable), type selector (Report/Manuscript/Whitepaper/Case Report), citation style picker
- **Section list**: Expandable accordion cards, one per section
  - Section heading (editable)
  - Key points list (editable, add/remove)
  - Subsection headings (editable, add/remove)
  - Drag-drop reorder (same framer-motion Reorder as slides)
- **Bottom bar**: "Generate Document" button + estimated page count

### 5.3 Backend: Doc Endpoints

#### [NEW] `backend/app/api/v1/endpoints/docs.py`

Mirror structure of `slides.py`:
- `POST /docs/outline` → generate outline
- `POST /docs/generate` → generate DOCX (SSE progress)  
- `GET /docs/download/{job_id}` → download DOCX

---

## 6. Design Intelligence Engine

This is the algorithmic layer that ensures professional quality. It lives entirely inside `slide_service.py` as the `DesignEngine` class.

### 6.1 Theme System

#### [NEW] `backend/app/services/design_engine.py` (~350 lines)

```python
class DesignEngine:
    """Rule-based design system for slide generation.
    
    The AI generates CONTENT. This engine handles VISUAL DESIGN.
    Never let the AI choose fonts, sizes, or colors directly.
    """
    
    # ========================================
    # THEME DEFINITIONS (10 curated palettes)
    # ========================================
    
    THEMES = {
        "ocean_gradient": {
            "name": "Ocean Gradient",
            "bg_dark": "065A82",      # Title slide background
            "bg_light": "F8FBFD",     # Content slide background
            "primary": "1C7293",      # Section headers, accents
            "accent": "21295C",       # Callout backgrounds, icons
            "text_on_dark": "FFFFFF", # Text on dark backgrounds
            "text_on_light": "2D3436",# Body text on light backgrounds
            "muted": "636E72",        # Captions, metadata
            "success": "00B894",      # Positive data callouts
            "warning": "FDCB6E",      # Warning highlights
            "header_font": "Georgia",
            "body_font": "Calibri",
        },
        "forest_moss": {
            "name": "Forest & Moss",
            "bg_dark": "2C5F2D",
            "bg_light": "F5F5F0",
            "primary": "97BC62",
            "accent": "2C5F2D",
            "text_on_dark": "FFFFFF",
            "text_on_light": "2D3436",
            "muted": "636E72",
            "success": "00B894",
            "warning": "FDCB6E",
            "header_font": "Cambria",
            "body_font": "Calibri",
        },
        "coral_energy": {
            "name": "Coral Energy",
            "bg_dark": "2F3C7E",
            "bg_light": "FFF9F5",
            "primary": "F96167",
            "accent": "F9E795",
            "text_on_dark": "FFFFFF",
            "text_on_light": "2D3436",
            "muted": "636E72",
            "success": "00B894",
            "warning": "FDCB6E",
            "header_font": "Arial Black",
            "body_font": "Arial",
        },
        "teal_trust": {
            "name": "Teal Trust",
            "bg_dark": "028090",
            "bg_light": "F0FAFA",
            "primary": "00A896",
            "accent": "02C39A",
            "text_on_dark": "FFFFFF",
            "text_on_light": "2D3436",
            "muted": "636E72",
            "success": "02C39A",
            "warning": "FDCB6E",
            "header_font": "Trebuchet MS",
            "body_font": "Calibri",
        },
        "charcoal_minimal": {
            "name": "Charcoal Minimal",
            "bg_dark": "212121",
            "bg_light": "F8F8F8",
            "primary": "36454F",
            "accent": "F2F2F2",
            "text_on_dark": "F2F2F2",
            "text_on_light": "212121",
            "muted": "888888",
            "success": "4CAF50",
            "warning": "FF9800",
            "header_font": "Arial Black",
            "body_font": "Calibri Light",
        },
        # ... 5 more themes (berry_cream, sage_calm, cherry_bold, etc.)
    }
    
    # ========================================
    # TYPOGRAPHY CONSTANTS
    # ========================================
    
    TITLE_SIZE = Pt(36)
    SUBTITLE_SIZE = Pt(20)
    HEADING_SIZE = Pt(28)
    BODY_SIZE = Pt(16)
    CAPTION_SIZE = Pt(11)
    SPEAKER_NOTE_SIZE = Pt(12)
    
    # ========================================
    # LAYOUT ENGINE
    # ========================================
    
    def select_layout(self, slide: dict, prev_layout: str = None, 
                       prev_prev_layout: str = None) -> str:
        """Rule-based layout selection (never 3 consecutive same layouts)"""
        bullets = slide.get("bullets", [])
        has_image = bool(slide.get("image_prompt"))
        has_data = slide.get("data") is not None
        word_count = sum(len(b.split()) for b in bullets)
        
        # Hard rules
        if slide.get("slide_number") == 1:
            return "title"
        if has_data:
            candidate = "data_callout"
        elif bullets == [] and has_image:
            candidate = "image_full"
        elif has_image and word_count < 40:
            candidate = "two_column"
        elif len(bullets) > 5:
            candidate = "bullets_only"
        elif has_image:
            candidate = "two_column"
        else:
            candidate = "bullets_only"
        
        # Anti-repetition: no 3 in a row
        if candidate == prev_layout == prev_prev_layout:
            alternatives = ["two_column", "data_callout", "bullets_only"]
            alternatives = [a for a in alternatives if a != candidate]
            candidate = alternatives[0]
        
        return candidate
    
    def analyze_and_adjust(self, outline: dict) -> dict:
        """Pre-assembly density and layout analysis"""
        slides = outline["slides"]
        adjusted = []
        prev = None
        prev_prev = None
        
        for slide in slides:
            # Density check: split slides with >6 bullets
            bullets = slide.get("bullets", [])
            if len(bullets) > 6:
                # Split into two slides
                mid = len(bullets) // 2
                slide1 = {**slide, "bullets": bullets[:mid], 
                          "title": slide["title"] + " (1/2)"}
                slide2 = {**slide, "bullets": bullets[mid:],
                          "title": slide["title"] + " (2/2)",
                          "slide_number": slide["slide_number"] + 0.5}
                adjusted.extend([slide1, slide2])
            else:
                adjusted.append(slide)
            
            # Update layout based on rules
            slide["layout"] = self.select_layout(slide, prev, prev_prev)
            prev_prev = prev
            prev = slide["layout"]
        
        # Renumber
        for i, slide in enumerate(adjusted):
            slide["slide_number"] = i + 1
        
        outline["slides"] = adjusted
        return outline
    
    # ========================================
    # PPTX ASSEMBLY (python-pptx)
    # ========================================
    
    def assemble_pptx(self, outline: dict, content: list, 
                       images: dict, theme: dict) -> bytes:
        """Build professional PPTX using python-pptx"""
        prs = Presentation()
        prs.slide_width = Inches(13.333)  # 16:9
        prs.slide_height = Inches(7.5)
        
        for i, slide_data in enumerate(outline["slides"]):
            layout = slide_data.get("layout", "bullets_only")
            image_bytes = images.get(i)
            
            if layout == "title":
                self._build_title_slide(prs, slide_data, theme, image_bytes)
            elif layout == "two_column":
                self._build_two_column_slide(prs, slide_data, theme, image_bytes)
            elif layout == "data_callout":
                self._build_data_callout_slide(prs, slide_data, theme)
            elif layout == "image_full":
                self._build_image_full_slide(prs, slide_data, theme, image_bytes)
            else:
                self._build_bullets_slide(prs, slide_data, theme)
            
            # Add speaker notes
            if slide_data.get("speaker_notes"):
                slide = prs.slides[-1]
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = slide_data["speaker_notes"]
        
        # Add slide numbers to all content slides
        self._add_slide_numbers(prs, theme)
        
        # Export to bytes
        output = io.BytesIO()
        prs.save(output)
        return output.getvalue()
    
    def _build_title_slide(self, prs, data, theme, image_bytes=None):
        """Dark background, centered title, optional background image"""
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)
        
        # Dark background
        bg = slide.background
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor.from_string(theme["bg_dark"])
        
        # Background image (dimmed) if available
        if image_bytes:
            slide.shapes.add_picture(
                io.BytesIO(image_bytes), 
                Inches(0), Inches(0),
                prs.slide_width, prs.slide_height
            )
            # Add dark overlay
            overlay = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, 
                Inches(0), Inches(0),
                prs.slide_width, prs.slide_height
            )
            overlay.fill.solid()
            overlay.fill.fore_color.rgb = RGBColor.from_string(theme["bg_dark"])
            # Set transparency via XML
        
        # Title text
        txBox = slide.shapes.add_textbox(
            Inches(1.5), Inches(2.5), Inches(10), Inches(2)
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = data["title"]
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = RGBColor.from_string(theme["text_on_dark"])
        p.font.name = theme["header_font"]
        p.alignment = PP_ALIGN.CENTER
        
        # Subtitle
        if data.get("subtitle"):
            p2 = tf.add_paragraph()
            p2.text = data["subtitle"]
            p2.font.size = Pt(20)
            p2.font.color.rgb = RGBColor.from_string(theme["text_on_dark"])
            p2.font.name = theme["body_font"]
            p2.alignment = PP_ALIGN.CENTER
    
    def _build_two_column_slide(self, prs, data, theme, image_bytes=None):
        """Text left (60%), image right (40%)"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        # Light background
        bg = slide.background
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor.from_string(theme["bg_light"])
        
        # Left column: Title + bullets (60% width)
        left_x, left_w = Inches(0.8), Inches(7)
        
        # Title
        title_box = slide.shapes.add_textbox(left_x, Inches(0.5), left_w, Inches(1))
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = data["title"]
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = RGBColor.from_string(theme["primary"])
        p.font.name = theme["header_font"]
        
        # Bullets
        bullet_box = slide.shapes.add_textbox(left_x, Inches(1.8), left_w, Inches(5))
        tf = bullet_box.text_frame
        tf.word_wrap = True
        for j, bullet in enumerate(data.get("bullets", [])):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.text = f"• {bullet}"
            p.font.size = Pt(16)
            p.font.color.rgb = RGBColor.from_string(theme["text_on_light"])
            p.font.name = theme["body_font"]
            p.space_after = Pt(8)
        
        # Right column: Image (40% width)
        if image_bytes:
            img_x = Inches(8.2)
            img_w = Inches(4.8)
            img_h = Inches(5.5)
            slide.shapes.add_picture(
                io.BytesIO(image_bytes),
                img_x, Inches(1), img_w, img_h
            )
    
    # ... _build_data_callout_slide, _build_image_full_slide, 
    #     _build_bullets_slide follow same pattern
```

**Where**: `backend/app/services/design_engine.py`

### 6.2 Design Rules Summary

| Rule | Enforcement | Fallback |
|------|------------|----------|
| **No 3 same layouts in a row** | `select_layout()` checks prev+prev_prev | Force layout rotation |
| **Max 6 bullets per slide** | `analyze_and_adjust()` auto-splits | Split into 2 slides |
| **Title sandwich** (dark/light/dark) | First + last slides get `bg_dark`, rest get `bg_light` | Hard-coded in assembly |
| **Typography hierarchy** | Constants: 44pt/28pt/16pt/11pt | Never AI-chosen |
| **0.5" margins** | Built into positional math (`Inches(0.8)` minimum x) | Hard-coded |
| **No accent lines under titles** | Never generated by assembly code | Not in codepath |
| **Text contrast** | `text_on_dark` vs `text_on_light` picked by background | Auto from theme |
| **Varied layouts** | Layout engine rotates through 5 types | Anti-repetition guard |
| **Image sizing** | Always `cover` mode, never stretch | Fixed aspect ratio crop |
| **White space** | 0.3" minimum between elements | Built into positional constants |

---

## 7. Anti-Regression Strategy

### 7.1 Test Architecture

```
backend/tests/
├── regression/
│   ├── test_mermaid.py            # [EXISTING] 341 lines, 21 tests
│   └── test_slides.py            # [NEW] Slide regression tests
├── test_slide_service.py         # [NEW] Unit tests
├── test_doc_service.py           # [NEW] Unit tests
├── test_design_engine.py         # [NEW] Design rule tests
└── test_mermaid_validator.py     # [EXISTING] 169 lines, 12 tests
```

### 7.2 Regression Test: Slides

#### [NEW] `backend/tests/regression/test_slides.py` (~200 lines)

```python
"""
Regression Test Suite — Slide Generation

Ensures design intelligence rules are never violated.
Run time target: <500ms (no API calls, mock AI responses)

Usage:
    pytest tests/regression/test_slides.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.design_engine import DesignEngine

class TestLayoutEngine:
    """Test that layout rules are always enforced"""
    
    @pytest.fixture
    def engine(self):
        return DesignEngine()
    
    def test_first_slide_always_title(self, engine):
        """First slide must ALWAYS be title layout"""
        slide = {"slide_number": 1, "bullets": ["a", "b"], "image_prompt": "test"}
        assert engine.select_layout(slide) == "title"
    
    def test_no_three_same_layouts(self, engine):
        """Never 3 consecutive identical layouts"""
        slide = {"slide_number": 5, "bullets": ["a"], "image_prompt": None}
        result = engine.select_layout(slide, prev_layout="bullets_only", 
                                       prev_prev_layout="bullets_only")
        assert result != "bullets_only"
    
    def test_data_callout_for_data_slides(self, engine):
        """Slides with data field get data_callout layout"""
        slide = {"slide_number": 3, "bullets": [], 
                 "data": {"value": "85%", "label": "Response Rate"},
                 "image_prompt": None}
        assert engine.select_layout(slide) == "data_callout"
    
    def test_two_column_for_image_plus_text(self, engine):
        """Slides with image and short text get two_column"""
        slide = {"slide_number": 3, "bullets": ["short point", "another"], 
                 "image_prompt": "test image"}
        assert engine.select_layout(slide) == "two_column"


class TestDensityAnalysis:
    """Test that content density rules are enforced"""
    
    @pytest.fixture
    def engine(self):
        return DesignEngine()
    
    def test_split_overloaded_slides(self, engine):
        """Slides with >6 bullets get split into two"""
        outline = {
            "slides": [
                {"slide_number": 1, "layout": "title", "title": "Title", 
                 "bullets": []},
                {"slide_number": 2, "layout": "bullets_only", "title": "Dense",
                 "bullets": ["b1","b2","b3","b4","b5","b6","b7","b8"]}
            ]
        }
        adjusted = engine.analyze_and_adjust(outline)
        # Should now have 3 slides (title + 2 content)
        assert len(adjusted["slides"]) == 3
    
    def test_slide_renumbering(self, engine):
        """After splitting, slide numbers are sequential"""
        outline = {
            "slides": [
                {"slide_number": 1, "layout": "title", "title": "Title", "bullets": []},
                {"slide_number": 2, "layout": "bullets_only", "title": "Dense",
                 "bullets": ["b1","b2","b3","b4","b5","b6","b7","b8"]}
            ]
        }
        adjusted = engine.analyze_and_adjust(outline)
        numbers = [s["slide_number"] for s in adjusted["slides"]]
        assert numbers == [1, 2, 3]


class TestThemeSystem:
    """Test theme consistency"""
    
    @pytest.fixture
    def engine(self):
        return DesignEngine()
    
    def test_all_themes_have_required_keys(self, engine):
        """Every theme must have all required color keys"""
        required = ["bg_dark", "bg_light", "primary", "accent", 
                    "text_on_dark", "text_on_light", "muted",
                    "header_font", "body_font"]
        for name, theme in engine.THEMES.items():
            for key in required:
                assert key in theme, f"Theme {name} missing key: {key}"
    
    def test_all_themes_valid_hex(self, engine):
        """All color values must be valid 6-char hex"""
        hex_keys = ["bg_dark", "bg_light", "primary", "accent", 
                    "text_on_dark", "text_on_light", "muted"]
        for name, theme in engine.THEMES.items():
            for key in hex_keys:
                value = theme[key]
                assert len(value) == 6 and all(c in "0123456789ABCDEFabcdef" for c in value), \
                    f"Theme {name}.{key} = '{value}' is not valid hex"
    
    def test_default_theme_exists(self, engine):
        """ocean_gradient must always be available as fallback"""
        assert "ocean_gradient" in engine.THEMES


class TestPPTXAssembly:
    """Test that generated PPTX files are valid"""
    
    @pytest.fixture
    def engine(self):
        return DesignEngine()
    
    def test_pptx_has_correct_slide_count(self, engine):
        """Generated PPTX has same slide count as outline"""
        outline = {
            "title": "Test", "theme": "ocean_gradient",
            "slides": [
                {"slide_number": 1, "layout": "title", "title": "Title",
                 "bullets": [], "speaker_notes": "Notes"},
                {"slide_number": 2, "layout": "bullets_only", "title": "Content",
                 "bullets": ["Point 1", "Point 2"], "speaker_notes": "More notes"}
            ]
        }
        pptx_bytes = engine.assemble_pptx(
            outline=outline, content=outline["slides"], 
            images={}, theme=engine.THEMES["ocean_gradient"]
        )
        
        # Parse and check
        from pptx import Presentation
        import io
        prs = Presentation(io.BytesIO(pptx_bytes))
        assert len(prs.slides) == 2
    
    def test_pptx_is_valid_file(self, engine):
        """Generated bytes are a valid PPTX (ZIP) file"""
        outline = {
            "title": "Test", "theme": "ocean_gradient",
            "slides": [{"slide_number": 1, "layout": "title", "title": "Test", 
                        "bullets": []}]
        }
        pptx_bytes = engine.assemble_pptx(
            outline=outline, content=outline["slides"],
            images={}, theme=engine.THEMES["ocean_gradient"]
        )
        assert pptx_bytes[:4] == b'PK\x03\x04'  # ZIP magic bytes


class TestPerformance:
    """Ensure design engine is fast"""
    
    def test_layout_selection_speed(self):
        """Layout selection for 20 slides in <5ms"""
        import time
        engine = DesignEngine()
        slides = [{"slide_number": i, "bullets": ["a","b","c"], 
                   "image_prompt": "test" if i % 2 == 0 else None,
                   "data": None}
                  for i in range(1, 21)]
        
        start = time.perf_counter()
        prev = None
        prev_prev = None
        for s in slides:
            layout = engine.select_layout(s, prev, prev_prev)
            prev_prev = prev
            prev = layout
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 5, f"Layout selection took {elapsed:.2f}ms (target: <5ms)"
```

### 7.3 Anti-Regression Rules for Existing Features

Every time we add code to the backend, we must verify nothing breaks:

```bash
# MANDATORY pre-commit check (add to .github/workflows/ci.yml or run manually)
cd /Users/mac/Desktop/phhh/backend

# 1. Existing mermaid tests
pytest tests/regression/test_mermaid.py -v --tb=short

# 2. Existing mermaid validator tests
pytest tests/test_mermaid_validator.py -v --tb=short

# 3. New slide tests
pytest tests/regression/test_slides.py -v --tb=short

# 4. New service tests
pytest tests/test_slide_service.py -v --tb=short
pytest tests/test_design_engine.py -v --tb=short

# 5. Full regression suite
pytest tests/regression/ -v --tb=short

# 6. Import smoke test (catches circular imports)
python -c "from app.services.slide_service import SlideService; print('OK')"
python -c "from app.services.design_engine import DesignEngine; print('OK')"
python -c "from app.services.doc_service import DocService; print('OK')"
```

### 7.4 Anti-Regression Checklist (Manual)

Before any PR or deployment:

| Check | How | Pass Criteria |
|-------|-----|---------------|
| **Mermaid still renders** | Send "draw RAAS pathway" → check diagram appears | Diagram renders with no error |
| **Export still works** | Export any chat as DOCX → open in Word | Valid DOCX with content |
| **Deep Research still works** | Run a deep research query → wait for completion | Report generates with sources |
| **Chat streaming works** | Send any message → response streams | No 422/500 errors |
| **Image generation works** | Request "show me aspirin structure" | Image renders inline |
| **All regression tests pass** | `pytest tests/regression/ -v` | 0 failures |

### 7.5 CI Pipeline Guard (Recommended)

#### [NEW] `.github/workflows/regression.yml`

```yaml
name: Regression Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pip install python-pptx pytest
      - run: cd backend && pytest tests/regression/ -v --tb=short
        env:
          PYTHONPATH: backend
```

This blocks any merge that breaks regression tests.

---

## 8. Verification Plan

### Phase A Verification

```bash
# Unit tests (no API calls, all mocked)
cd /Users/mac/Desktop/phhh/backend
pytest tests/test_design_engine.py -v
pytest tests/regression/test_slides.py -v

# Integration test (requires API keys)
pytest tests/test_slide_service.py -v

# Import smoke test
python -c "from app.services.slide_service import SlideService; print('✅ SlideService')"
python -c "from app.services.design_engine import DesignEngine; print('✅ DesignEngine')"
```

### Phase B Verification

```bash
# Image generation test (requires Pollinations API key)
pytest tests/test_slide_service.py::test_pptx_with_images -v

# Manual: Generate a 10-slide deck with images
# Open in PowerPoint → verify images are embedded and properly sized
```

### Phase C Verification

```bash
pytest tests/test_doc_service.py -v

# Manual: Generate a report → open DOCX → verify:
# - Table of Contents present and clickable
# - Page numbers in footer
# - Heading hierarchy (H1, H2, H3)
# - "Generated by Benchside" footer
```

### Full Regression (all phases)

```bash
cd /Users/mac/Desktop/phhh/backend
pytest tests/regression/ -v --tb=short
# Target: ALL existing + new tests pass, 0 regressions
```

---

## Implementation Timeline

```
Week 1-2:  Phase A — SlideService + DesignEngine + SlideOutlineEditor + SlideProgress
Week 3:    Phase B — Pollinations image gen per slide + image fallback strategy  
Week 4-5:  Phase C — DocService + DocOutlineEditor + DocProgress
Week 5:    Anti-regression tests + CI pipeline setup
```

**Total: ~55-65 hours over 5 weeks**
