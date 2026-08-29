# AGENTS.md

## Roles
- planner: Claude (this session) — architecture, task specs, bug diagnosis, review. No code.
- core_agent: Claude Sonnet 4.6 — writes `core/` (processing logic), `tests/`.
- gui_agent: Gemini 3.1 Pro — writes `gui/` (PySide6 UI), `main.py` wiring.

## Stack
- Lang: Python 3.11+, Windows-only target.
- GUI: PySide6 (LGPL, not PyQt6).
- PDF: PyMuPDF (fitz), pikepdf, pypdf, pdf2docx.
- Office conv: bundled portable LibreOffice via subprocess (`office_bridge.py`), headless.
- Packaging: PyInstaller (single exe, bundles portable LibreOffice).
- Tests: pytest.

## Layout
```
pdf_toolkit/
├── AGENTS.md   # this file, root, always read first
├── ai-docs/
│   ├── context.md        # current state, read at start of new session
│   ├── project-plan.md   # phases, status
│   └── changelog.md      # major features/architecture only
├── core/       # core_agent. Pure functions. No Qt imports. No file dialogs. No print().
├── gui/        # gui_agent. PySide6 only. No PDF-processing logic — calls core/ only.
├── main.py     # entry point, wires gui -> core
├── tests/      # core_agent. pytest, one file per core module.
└── requirements.txt
```

## Contract (core <-> gui)
- core functions: primitive args only (str, list, int, dict). Return output path(s) or raise.
- Exceptions: `PDFToolkitError` base, subclasses: `ConversionError`, `InvalidFileError`, `LibreOfficeNotFoundError`.
- Every core public fn: docstring w/ params, return, exceptions raised.
- gui never touches PDF libs directly.
- Output location: always user-chosen via save dialog (no default output folder).
- Processing: synchronous, blocking OK. Show modal indeterminate progress dialog during run (no threading required).

## Config
- Decisions log: see docs/context.md "Locked decisions" — do not re-litigate without asking user.

## Git
- Commit format: `TYPE - {files}: {summary}`
  - TYPE: FEAT | FIX | REFACTOR | TEST | DOCS | CHORE
  - example: `FEAT - core/convert_to.py: add pdf_to_images`
- Commit ONLY when explicitly requested by user. Never auto-commit.

## Doc update rules
- docs/changelog.md: update only on major completed feature or architecture change (not every task).
- docs/context.md: keep current, rewrite freely as project evolves.
- docs/project-plan.md: update phase status as phases complete/change.

## Completion report (required after every task)
On finishing any task, report back:
- Files created/modified (path list).
- What was built — 1 line per function/component.
- Key implementation decisions (esp. anything not explicitly specified in the task prompt — e.g. library choice, edge-case handling).
- Deviations from spec, if any, and why.
- Known issues / things not handled / TODOs.
- For core_agent: test results (pass/fail count).
- For gui_agent: any core/ functions it needed but didn't exist yet, or assumptions made about core's return values/exceptions.
Keep it concise — bullet points, no prose padding.