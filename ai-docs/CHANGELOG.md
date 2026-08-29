# CHANGELOG

Format: `[DATE] TYPE: summary`
Log only major completed features or architecture changes. Not per-task.

## Unreleased
- [2026-08-29] FEAT: core convert module complete — pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, pdf_to_images, docx_to_pdf, xlsx_to_pdf, pptx_to_pdf, images_to_pdf. 47 tests (41 passed/6 skipped/0 failed) after correction pass. Office conversions via LibreOffice subprocess bridge (office_bridge.py); PDF->Word via pdf2docx directly.
- [2026-08-29] FEAT: GUI shell complete — sidebar (Convert active, 4 categories disabled), HomePage tool grid, reusable ConvertToolPage (independent/combine modes), DropZone, MainWindow routing. Convert/Organize/Optimize/Edit/Security nav in place, only Convert wired.
- [2026-08-29] ARCHITECTURE/FEAT: Rebuilt Convert workflow into a unified single-screen dashboard (`convert_page.py`), replacing the previous drill-down `HomePage` and `ConvertToolPage`. Implemented a global dark theme (`styles/theme.py`) and dynamic SVG vector icons (`utils/icons.py`) to precisely match the target mockup.
- [2026-08-29] FEAT: Organize tools complete — merge, split (with live range preview), extract pages, delete pages, reorder pages, rotate pages. Shared PageThumbnailGrid component (click-select, drag-reorder) built for page-level tools. 6/6 tools verified working via headless UI test.