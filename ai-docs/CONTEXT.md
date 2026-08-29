# CONTEXT

PDF toolkit desktop app (iLovePDF clone). Python + PySide6, Windows-only. See ../AGENTS.md for stack/roles/contract, project-plan.md (same dir) for phases/status.

## Locked decisions
- Layout: single window, sidebar dashboard, all tools visible.
- Batch processing: default on where applicable (merge, compress, convert).
- OS: Windows only.
- Output: user picks save location every run, no default output folder.
- Processing: synchronous + blocking; modal indeterminate spinner during run; no multithreading.
- Flagship/build-first category: Convert tools (PDF<->Word/Excel/PPT/JPG).
- Office<->PDF conversion: bundled portable LibreOffice (not user-installed), invoked headless via subprocess.
- GUI lib: PySide6 (not PyQt6, license).

## Feature scope (core modules)
- Organize: merge_pdfs, split_pdf, extract_pages, delete_pages, reorder_pages, rotate_pages
- Optimize: compress_pdf
- Convert to PDF: docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf
- Convert from PDF: pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images
- Edit: add_watermark, add_page_numbers
- Security: protect_pdf, unlock_pdf

## Current status
Phase: 1 and 2 done. Phase 3 (Organize tools) next — not yet started. Phase 2 not yet independently file-verified by planner (see project-plan.md note).

## Open items / not yet decided
- Exact LibreOffice bundling mechanism for PyInstaller (deferred to Phase 5).
- GUI page structure within sidebar (per-tool view details) — deferred to Phase 2 spec.