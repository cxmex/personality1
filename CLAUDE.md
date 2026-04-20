# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Run locally (default port 8000)
uvicorn main:app --reload

# Run on a specific port
uvicorn main:app --reload --port 3000

# Install dependencies
pip install -r requirements.txt
```

There are no tests, linters, or build steps configured.

## Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Validation:** Pydantic v2 (with email support)
- **HTTP client:** httpx (async, used to call Supabase REST API directly)
- **Database:** Supabase (accessed via raw REST + `httpx`, not the `supabase-py` client — despite `supabase` being in requirements.txt, it is unused)
- **Python version:** 3.x (standard async/await)

## Architecture

Single-file backend (`main.py`) serving both the API and static HTML pages. No templating — HTML files are read from disk and returned as `HTMLResponse`.

### Data flow

1. HTML pages (one per position) collect answers via frontend JS
2. Frontend POSTs to `/api/submit` with participant info + answers
3. Backend scores the test via `calculate_*()` functions
4. Results are saved to three Supabase tables (`participants` → `answers` → `results`) and returned in the response

### Supabase access

All Supabase calls go through `save_to_supabase()` using `httpx.AsyncClient` with hardcoded `SUPABASE_URL` and `SUPABASE_KEY` (anon key) at the top of `main.py`. Supabase write failures are caught and logged but do not abort the request.

### Positions

Three job positions defined in the `POSITIONS` dict (`almacen`, `ventas_mostrador`, `pueblaventas`). All positions run the same 6 tests: `disc`, `big5`, `mbti`, `allport`, `terman`, `competencias`.

### Adding a new position or test

- **New position:** Add entry to `POSITIONS` dict + create an HTML file + add a route to serve it.
- **New test type:** Add a question list (`*_QUESTIONS`), a `calculate_*()` function, a branch in `/api/questions/{test_type}`, and a branch in `/api/submit`.

## Coding Conventions

- All endpoints are `async def`
- API routes live under `/api/` prefix; HTML page routes are at top-level paths (e.g., `/almacen`, `/dashboard`)
- Routes are grouped with `# ========== SECTION NAME ==========` comments
- All user-facing text (questions, descriptions, docstrings) is in Spanish
- Scoring logic lives in standalone `calculate_*()` functions
- CORS is fully open (`allow_origins=["*"]`)

## Deployment

Platform that reads `Procfile` (Render/Heroku). The `PORT` env var is injected at runtime.
