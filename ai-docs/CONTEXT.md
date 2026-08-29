# CONTEXT

PDF Toolbox — PDF toolkit desktop app (iLovePDF clone). Python + PySide6, Windows-only. See ../AGENTS.md for stack/roles/contract, project-plan.md (same dir) for phases/status.

## Locked decisions
- App name: PDF Toolbox
- Layout: single window, sidebar dashboard, all tools visible.
- Theme: dark mode only (MVP), professional/utility feel, one accent color (no multi-color UI).
- Color palette (hex):
  - Page bg: #121317
  - Surface (cards, sidebar): #1B1D22
  - Surface elevated (hover/active): #24262C
  - Border: #33353C
  - Text primary: #EAEAEC
  - Text secondary: #9497A0
  - Accent (active nav, primary buttons): #4C8DFF
  - Success: #34D399 | Error: #F87171 | Warning: #FBBF24
  - Text-on-accent (e.g. button label on #4C8DFF fill): #0A1830 (dark navy, not black/white)
- Batch processing: default on where applicable (merge, compress, convert).
- OS: Windows only.
- Output: user picks save location every run, no default output folder.
- Processing: synchronous + blocking; modal indeterminate spinner during run; no multithreading.
- Flagship/build-first category: Convert tools (PDF<->Word/Excel/PPT/JPG).
- Office<->PDF conversion: bundled portable LibreOffice (not user-installed), invoked headless via subprocess.
- GUI lib: PySide6 (not PyQt6, license).
- Organize tools page-selection UX: visual page-thumbnail grid (click to select, drag to reorder) — not text/range input. Applies to extract, delete, reorder, rotate (per-page), and split-by-ranges.

## Feature scope (core modules)
- Organize: merge_pdfs, split_pdf, extract_pages, delete_pages, reorder_pages, rotate_pages
- Optimize: compress_pdf
- Convert to PDF: docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf
- Convert from PDF: pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images
- Edit: add_watermark, add_page_numbers
- Security: protect_pdf, unlock_pdf

## Current status
Phase 1-3 core done. GUI redesigned to unified upload-first workflow (see PROJECT-PLAN.md GUI Redesign section), human-verified working. Phase 4 (Compress+Security) next.

## Open items / not yet decided
- Exact LibreOffice bundling mechanism for PyInstaller (deferred to Phase 5).
- GUI page structure within sidebar (per-tool view details) — deferred to Phase 2 spec.