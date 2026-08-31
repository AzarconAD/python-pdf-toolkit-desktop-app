# AGENTS.md

## Roles
- writer: developer (me), you (ai)
- planner: Claude — architecture, task specs, bug diagnosis, review. No code.
- core_agent: Claude Sonnet 4.6 — writes `core/` (processing logic), `tests/`.
- gui_agent: Gemini 3.1 Pro — writes `gui/` (PySide6 UI), `main.py` wiring.

## Stack
- Lang: Python 3.11+, Windows-only target.
- GUI: PySide6 (LGPL, not PyQt6).
- PDF: PyMuPDF (fitz), pikepdf, pypdf, pdf2docx.
- Office conv: bundled portable LibreOffice via subprocess (`office_bridge.py`), headless.
- Packaging: PyInstaller (single exe, bundles portable LibreOffice).
- Tests: pytest.
- Edits to existing files: provide only the changed code block(s) + exact location (function name / line context / before-after anchor). Do not reprint or rewrite entire files for partial changes. Full-file output only for brand-new files.

## Layout
```
pdf_toolkit/
├── AGENTS.md   # this file, root, always read first
├── ai-docs/
│   ├── CONTEXT.md        # current state, read at start of new session
│   ├── PROJECT-PLAN.md   # phases, status
│   ├── CHANGELOG.md      # major features/architecture only
│   └── CLEANUP.md        # cleanup-pass instructions
├── core/       # core_agent. Pure functions. No Qt imports. No file dialogs. No print().
├── gui/        # gui_agent. PySide6 only. No PDF-processing logic — calls core/ only.
│   ├── main_window.py
│   ├── pages/
│   │   └── workspace_page.py
│   ├── styles/
│   │   └── theme.py          # single source of truth for all hex colors — no hardcoded hex elsewhere
│   ├── utils/
│   │   ├── error_messages.py
│   │   ├── icons.py          # SVG->QIcon renderer, must reference theme.py constants
│   │   └── thumbnails.py
│   └── widgets/
│       ├── drop_zone.py
│       └── page_thumbnail_grid.py
├── main.py     # entry point, wires gui -> core
├── tests/      # core_agent. pytest, one file per core module.
└── requirements.txt
```
Note: sidebar.py, convert_page.py, organize_page.py deleted - superseded by workspace_page.py. Grep-confirmed zero refs.

## Contract (core <-> gui)
- core functions: primitive args only (str, list, int, dict). Return output path(s) or raise.
- Exceptions: `PDFToolkitError` base, subclasses: `ConversionError`, `InvalidFileError`, `LibreOfficeNotFoundError`.
- Every core public fn: docstring w/ params, return, exceptions raised.
- gui never touches PDF libs directly.
- Output location: always user-chosen via save dialog (no default output folder).
- Processing: synchronous, blocking OK. Show modal indeterminate progress dialog during run (no threading required).

## Config
- Decisions log: see ai-docs/CONTEXT.md "Locked decisions" — do not re-litigate without asking user.
- Task sizing (tiered):
  - Tier 1 (always isolated, one task per prompt, no exceptions): any core/ change, any file deletion/replacement, any architecture/routing change, anything affecting test counts.
  - Tier 2 (safe to batch): styling, icons, copy, spacing, single-widget visual tweaks.
  - Batched (Tier 2) completion reports must itemize each task's before/after evidence individually, in order — not one merged summary. Same evidence bar as a single task (literal grep/diff/test output, not "confirmed"/"verified" claims).
- core/ is off-limits to gui_agent, no exceptions, including trivial fixes (e.g. warning suppression). Flag mismatches/issues to planner instead of patching core directly.
- Planner writes agent-facing prompts dense/imperative, token-minimal, no prose padding. Human readability of the prompt is not a goal — agent comprehension is.

## Git
- Commit format: `TYPE - {files}: {summary}`
  - TYPE: FEAT | FIX | REFACTOR | TEST | DOCS | CHORE
  - example: `FEAT - core/convert_to.py: add pdf_to_images`
- Commit ONLY when explicitly requested by user. Never auto-commit.

## Doc update rules
- ai-docs/CHANGELOG.md: update only on major completed feature or architecture change (not every task).
- ai-docs/CONTEXT.md: keep current, rewrite freely as project evolves.
- ai-docs/PROJECT-PLAN.md: update phase status as phases complete/change.

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
Do not claim "no deviations" without re-reading the actual spec section it applies to first (esp. file/module structure, function placement, naming) — a wrong confident claim is worse than flagging uncertainty.