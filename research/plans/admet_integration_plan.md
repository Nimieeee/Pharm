# Implementation Plan: Gold Standard ADMET Evolution (V6)

Deliver a world-class ADMET experience and a hardened chat export system, ensuring high-fidelity data handling and perfect UI accessibility.

## Proposed Changes

### [Backend - Science & Interpretation]

#### [MODIFY] [admet_service.py](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py)
- **AI Medicinal Chemist**: Full integration of `AIService` from the container using `@property` lazy loading.
- **SDF Intelligence**: Refactor `extract_smiles_from_sdf` to return `[{"smiles": "...", "name": "..."}]` by capturing molecule names (first line or `_Name` field).
- **Naming Context**: Propagate molecule names through `predict_admet` and `generate_report`.

#### [MODIFY] [admet_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py)
- **[NEW] Heuristic Interpretation Engine**:
    - Implement `_get_interpretation(endpoint, value)` to map scores to status symbols (✅, ⚠️, ❌).
    - Map toxicity scores (DILI, Ames, etc.) and likeness scores (QED, HIA) to appropriate thresholds.
- **Header Alignment**: Use legacy ADMETlab 3.0 abbreviations (HIA, BBB, DILI, hERG) as Markdown labels.
- **AI interpretation**: Add a `> [!TIP] AI Interpretation` section to the "Key Insights" using the medicinal chemistry LLM.

### [Frontend - UI/UX & Reliability]

#### [MODIFY] [ChatMessage.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/chat/ChatMessage.tsx)
- **[FIX] Export Reliability**: Replace brittle `window.location` parsing for `conversationId` with `useChatContext()`.
- **Validation**: Source the conversation ID from the authoritative context state to avoid 404/Missing ID errors.

#### [MODIFY] [HubLayout.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/HubLayout.tsx)
- **Theme-Aware Grid**: Update background dots to be visible in BOTH modes (light dots on dark, dark dots on light).

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)
- **Accessibility Fix**: Update text colors (e.g., "ADMET Profile Complete") to `text-slate-900 dark:text-white`.
- **Dynamic Suggestions**: 
    - [NEW] `frontend/src/constants/drugPool.ts` with 500+ FDA drugs.
    - Randomize the 4 suggestions on every mount/refresh.
- **Name Display**: Show extracted molecule name prominently in results.

#### [MODIFY] [ADMETPropertyCard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/ADMETPropertyCard.tsx)
- **Contrast Polish**: Ensure all labels and values use theme-aware contrast (dark slate on light, light slate on dark).

---

## Verification Plan

### Automated Tests
- **SDF Name Extraction**: `pytest tests/regression/test_admet_naming.py`.
- **Interpretation Logic**: `tests/regression/test_admet_thresholds.py`.

### Manual Verification
1.  **Chat Export**: Verify export works immediately upon starting a new chat.
2.  **ADMET Status**: Confirm that red/green badges appear correctly for toxic/safe compounds.
3.  **Grid Toggle**: Verify dots are visible and aesthetic in both Light and Dark modes.
4.  **Suggestion Shuffling**: confirm drug suggestions change on refresh.
