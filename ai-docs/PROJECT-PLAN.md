# PROJECT PLAN

## Phases
1. Core skeleton + Convert module (core_agent) — STATUS: done (47 tests, 41 passed/6 skipped/0 failed after correction pass; convert_to.py=PDF→other, convert_from.py=other→PDF per spec)
2. GUI shell: sidebar dashboard + Convert views (gui_agent) — STATUS: done (module swap + import corrections verified, routing manually confirmed)
3. Organize tools: merge/split/extract/delete/reorder/rotate (core_agent -> gui_agent) — STATUS: pending
4. Compress + Security: compress/protect/unlock/watermark/page_numbers (core_agent -> gui_agent) — STATUS: pending
5. Polish + packaging: PyInstaller, bundle portable LibreOffice, icons, error states, styling — STATUS: pending

## Phase 1 detail (complete)
Scope: core/utils.py, core/office_bridge.py, core/convert_to.py, core/convert_from.py, tests/.
No GUI code. office_bridge resolves soffice.exe via env var / common paths for now (bundling deferred to phase 5).
Functions built: pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images, docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf.
Result: 9/9 tests passing, no deviations from spec. pdf_to_docx uses pdf2docx directly (better quality than LibreOffice for Word); xlsx/pptx via office_bridge. Subprocess and fitz properly mocked in tests (no LibreOffice required to run test suite).
Full task spec: see conversation log / ../AGENTS.md contract rules.

## Phase 2 detail (complete, revised)
Scope: GUI shell (sidebar dashboard) + Convert tool views, wired to Phase 1 core functions.
Original structure (separate HomePage + ConvertToolPage) went through 4 correction rounds — see prior note below. Then, during the theme/styling task, gui_agent unprompted merged HomePage+ConvertToolPage into a single unified convert_page.py to match the design mockup's single-screen layout, added gui/utils/icons.py (SVG->QIcon renderer), and restyled sidebar to a pill-shaped active state. This was scope creep relative to the styling-only task it was given, but the resulting layout is consistent with the approved mockup, so it was kept rather than reverted. App name was also incorrectly changed to "DocForge" during this pass and corrected back to "PDF Toolbox".
Verification status: app confirmed boots cleanly (exit code 0, auto-quit timer test). Visual match to mockup pending user's own eyes-on check. Task 2g (hardcoded-hex-outside-theme.py audit) requested, not yet returned.
Prior Phase 2 (original structure) history: went through 4 correction rounds — (1) initial report only covered main.py, missing tasks 1-4; (2) core/ files edited without authorization (fitz->pymupdf deprecation fix, legitimate but broke 2 test mocks); (3) convert_to.py/convert_from.py had PDF→other and other→PDF swapped relative to spec, initially defended with a citation that actually disproved the claim; (4) corrected — module contents, imports, and test suite all verified post-fix. Final: 47 tests, 41 passed/6 skipped/0 failed. Not yet independently verified by planner via direct file upload.

## Phase 3 detail (next)
Scope: Organize tools (merge/split/extract/delete/reorder/rotate) — core functions + GUI wiring.

## Status legend
pending -> spec_written -> in_progress -> built -> reviewed -> done