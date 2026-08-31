# PROJECT PLAN

> **PROJECT STATUS: NOT FINISHED.** Phase 1-4 + Edit feature complete and verified. Phase 5 (packaging/polish) NOT STARTED — additional features/fixes planned first. Do not begin Phase 5 without explicit user go-ahead.


## Phases
1. Core skeleton + Convert module (core_agent) — STATUS: done (47 tests, 41 passed/6 skipped/0 failed after correction pass; convert_to.py=PDF→other, convert_from.py=other→PDF per spec)
2. GUI shell: sidebar dashboard + Convert views (gui_agent) — STATUS: done (module swap + import corrections verified, routing manually confirmed)
3. Organize tools: merge/split/extract/delete/reorder/rotate (core_agent -> gui_agent) — STATUS: done (GUI superseded by redesign)
4. Compress + Security: compress/protect/unlock/watermark/page_numbers (core_agent -> gui_agent) — STATUS: done
5. Polish + packaging: PyInstaller, bundle portable LibreOffice, icons, error states, styling — STATUS: pending

## Phase 1 detail (complete)
Scope: core/utils.py, core/office_bridge.py, core/convert_to.py, core/convert_from.py, tests/.
No GUI code. office_bridge resolves soffice.exe via env var / common paths for now (bundling deferred to phase 5).
Functions built: pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images, docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf.
Result: 9/9 tests passing, no deviations from spec. pdf_to_docx uses pdf2docx directly (better quality than LibreOffice for Word); xlsx/pptx via office_bridge. Subprocess and fitz properly mocked in tests (no LibreOffice required to run test suite).
Full task spec: see conversation log / ../AGENTS.md contract rules.

## Phase 2 detail (complete, revised)
Scope: GUI shell (sidebar dashboard) + Convert tool views, wired to Phase 1 core functions.
Original structure (separate HomePage + ConvertToolPage) went through 4 correction rounds — see prior note below. Then, during the theme/styling task, gui_agent unprompted merged HomePage+ConvertToolPage into a single unified convert_page.py to match the design mockup's single-screen layout, added gui/utils/icons.py (SVG->QIcon renderer), and restyled sidebar to a pill-shaped active state. This was scope creep relative to the styling-only task it was given, but the resulting layout is consistent with the approved mockup, so it was kept rather than reverted. App name was also incorrectly changed to "DocForge" during this pass and corrected back to "PDF ToolBox".
Verification status: app confirmed boots cleanly (exit code 0, auto-quit timer test). Visual match to mockup pending user's own eyes-on check. Task 2g (hardcoded-hex-outside-theme.py audit) requested, not yet returned.
Prior Phase 2 (original structure) history: went through 4 correction rounds — (1) initial report only covered main.py, missing tasks 1-4; (2) core/ files edited without authorization (fitz->pymupdf deprecation fix, legitimate but broke 2 test mocks); (3) convert_to.py/convert_from.py had PDF→other and other→PDF swapped relative to spec, initially defended with a citation that actually disproved the claim; (4) corrected — module contents, imports, and test suite all verified post-fix. Final: 47 tests, 41 passed/6 skipped/0 failed. Not yet independently verified by planner via direct file upload.

## Phase 3 detail (complete)
Scope: Organize tools (merge/split/extract/delete/reorder/rotate) — core functions + GUI wiring.
GUI wiring complete — sidebar Organize enabled, OrganizePage with 6 tool cards (Merge/Split/Extract/Delete/Reorder/Rotate), all wired to core.organize functions. Split tool includes live range preview (page grouping shown before commit, added after initial gap identified in review). Verified via full pytest suite (78 total, 72 passed, 6 skipped, 0 failed — unchanged from core-only count, as expected for GUI-layer work) plus a synthetic headless UI script exercising all 6 tools end-to-end. NOTE: The GUI portion of this phase is superseded by the GUI Redesign.

## GUI Redesign (complete)
Scope: Unified upload-first workflow replacing older paginated structures.
- UnifiedWorkspacePage 4-state workflow implemented: State 1 (Empty DropZone), State 2 (Loaded compact DropZone + File Previews), State 3 (Tool Controls + Grid Expansion), State 4 (Inline Results overlay with action buttons).
- Legacy views deleted: `sidebar.py`, `convert_page.py`, `organize_page.py` completely removed and grep-confirmed zero remaining references.
- Error Handling: New `gui/utils/error_messages.py` provides a friendly-error translation layer mapping backend exceptions to readable GUI strings.
- Validation: 78 tests total (72 passed, 6 skipped, 0 failed). Human click-through explicitly confirmed by user.
- Incident Log: Agent made unauthorized core edit (`pymupdf._g_out_message` suppression in `core/convert_to.py`), and bundled 8 subtasks simultaneously instead of adhering to the one-task-per-prompt rule. The core patch was reverted natively.

## Phase 4 detail (complete)
Scope: Compress + Security — compress_pdf, protect_pdf/unlock_pdf, add_watermark, add_page_numbers, add_image_watermark. Core functions + GUI wiring.
Core: core/security.py — all 5 functions. 103 passed / 6 skipped / 0 failed (109 total).
GUI: all 5 tools wired into Home grid (Optimize + Security tabs enabled). Watermark tool: Text/Image mode toggle (segmented pill), per-row labeled controls, live auto-preview (600ms debounced QTimer, temp-file render via render_page_thumbnail, inline "Rendering…" indicator, placeholder on empty inputs). Two-card side-by-side layout (settings card left, live preview card right).
compress_pdf fixes (3 root causes diagnosed + resolved):
  - Fix 1 (always-overwrite guard): `or scale < 1.0` in replace condition unconditionally replaced even when recompressed was larger — removed.
  - Fix 2 (ghost xref duplication): per-page `page.replace_image()` left orphaned old streams on shared-xref multi-page PDFs preventing garbage collection — replaced with document-level `doc.rewrite_images()`.
  - Fix 3 (PNG→JPEG inflation): `lossless=True` converted efficient PNG charts to JPEG, bloating output — changed to `lossless=False` (leave lossless images untouched).
  - Fix 4 (pymupdf serialiser overhead): pymupdf's writer inflates text/vector PDFs ~14% vs original — added Phase 2 pikepdf pass with `ObjectStreamMode.generate` to produce compact /ObjStm + /XRef streams. Net result: −9–12% on vector PDFs, −15–85% on image-heavy PDFs, never inflates.
requirements.txt: PyMuPDF pinned to >=1.26.1 (rewrite_images introduced in that release).
Other bugs fixed: incorrect-password infinite hang (missing IncorrectPasswordError import → silent NameError), mkstemp/get_unique_output_path temp-file collision (os.remove before core call, capture returned path).

## Edit feature (complete)
core/edit.py — apply_edits() (text/shape/image/draw/signature elements, unified schema), crop_page(), highlight_text(), redact_text() (genuine content removal, verified via get_text()). 33 tests, full suite 142 total/136 passed/6 skipped/0 failed. GUI: EditCanvas (QGraphicsView/Scene foundation) with 5 draggable/resizable/selectable element types, shared color picker, eraser (splits strokes on partial erase), text-selection infrastructure for Highlight/Redact, Crop mode, all using a working-copy pattern (temp file aliased as self.pdf_path, original preserved separately) so destructive ops (highlight/redact/crop) layer correctly before final apply_edits() Save. Signature adds first persistent user data (AppData/PDF ToolBox/signatures library). Multi-page support via per-item page_index tracking + visibility filtering in load_page(). EditPage routes standalone (bypasses UnifiedWorkspacePage's 4-state flow, canvas owns full viewport). Edit enabled in Home grid. Bugs fixed post-build: crop_page() argument unpacking, hardcoded placeholder colors (no picker existed - added shared active_color state), multi-page element visibility (elements had no page association, now tracked via page_index). Toolbar redesigned - old sprawling horizontal strip replaced with 64px left icon rail (grouped: color / insert tools / draw+eraser / select-text / crop) + contextual settings strip above canvas (shows only when active tool has extra settings, e.g. stroke width for Draw). Fixed regression introduced during restructure: rail buttons were stealing keyboard focus, breaking arrow-key page navigation - fixed via NoFocus policy on toolbar children, plus added a permanent visible Previous/Next + 'Page X of Y' indicator in EditPage header (previously navigation had zero visual affordance, arrow-keys-only). All 9 rail tools have hover tooltips. User-confirmed live: rail, page nav, and tooltips all work together correctly.

## Status legend
pending -> spec_written -> in_progress -> built -> reviewed -> done