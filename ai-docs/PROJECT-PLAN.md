# PROJECT PLAN

## Phases
1. Core skeleton + Convert module (core_agent) — STATUS: spec_written
2. GUI shell: sidebar dashboard + Convert views (gui_agent) — STATUS: pending
3. Organize tools: merge/split/extract/delete/reorder/rotate (core_agent -> gui_agent) — STATUS: pending
4. Compress + Security: compress/protect/unlock/watermark/page_numbers (core_agent -> gui_agent) — STATUS: pending
5. Polish + packaging: PyInstaller, bundle portable LibreOffice, icons, error states, styling — STATUS: pending

## Phase 1 detail (active)
Scope: core/utils.py, core/office_bridge.py, core/convert_to.py, core/convert_from.py, tests/.
No GUI code. office_bridge resolves soffice.exe via env var / common paths for now (bundling deferred to phase 5).
Functions: pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images, docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf.
Full task spec: see conversation log / ../AGENTS.md contract rules.

## Status legend
pending -> spec_written -> in_progress -> built -> reviewed -> done