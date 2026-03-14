# Implementation Plan: UI Refinements & UX Standardization

This plan addresses several user-reported UX issues and standardizes the interface across the Benchside platform.

## Proposed Changes

### [Component] Frontend Navigation & Theme

#### [MODIFY] [ResearchSidebar.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/ResearchSidebar.tsx)
- **Simplify Categories**: Unify hubs and tools into "Scientific Hubs" and "Resources". Remove redundant "ADMET Profiler" link.
- **Collapsible Support**: Add `isCollapsed` state and a toggle button to minimize the sidebar to icons only.
- **Consolidate Theme Toggle**: Remove the secondary theme toggle from the sidebar footer.

#### [MODIFY] [HubLayout.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/HubLayout.tsx)
- **Responsive Layout**: Adjust the main content container to shift/expand based on the sidebar's collapsed state.

---

### [Component] Visuals & Loading States

#### [MODIFY] [ParticleNetwork.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/landing/ParticleNetwork.tsx)
- **Visibility Fix**: Adjust z-index (`-10`) and ensuring the container in `page.tsx` doesn't have an opaque background that blocks the canvas.

#### [MODIFY] [LoadingAnimation.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/LoadingAnimation.tsx)
- **Branded Loading**: Integrate the `StreamingLogo` (animated Benchside logo) to replace the generic spinner for a more premium experience.

---

### [Component] Backend Report Processing

#### [MODIFY] [admet_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py)
- **Header Refinement**: Change "AI Interpretation" to "Medicinal Chemistry Insights".
- **Formatting Cleanup**: Add logic to strip excessive markdown asterisks and normalize spacing in the AI-generated text.

## Verification Plan

### Automated Tests
- Run existing regression tests on VPS to ensure processing logic remains stable:
  ```bash
  ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "cd /var/www/benchside-backend/backend && source .venv/bin/activate && pytest tests/regression/test_admet_service.py"
  ```

### Manual Verification
1. **Landing Page**: Verify particles are visible and interactive.
2. **Sidebar**: Test collapsing functionality and verify unified categories.
3. **Theme**: Confirm only one toggle remains in the hub interface.
4. **Loading Animation**: Start an analysis in Molecular Lab or Literature Search to view the new branding.
5. **ADMET Report**: Run analysis and verify the "Medicinal Chemistry Insights" section is clean and formatted correctly.
