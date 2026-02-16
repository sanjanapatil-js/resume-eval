# Backend (FastAPI) — Resume Evaluator

This folder contains a **FastAPI** backend that:

- Renders a **Jinja2** web UI (`templates/index.html`)
- Accepts a **Job Description** + **one or more PDF resumes**
- Extracts text from PDFs using **pdfplumber**
- Sends the JD + extracted resume text to **Groq LLM** to compute an ATS-style match
- Displays per-resume results plus a simple in-memory **leaderboard**

## Tech Stack

- **FastAPI** (web framework)
- **Uvicorn** (ASGI server)
- **Jinja2Templates** (server-side HTML rendering)
- **python-multipart** (form + file uploads)
- **pdfplumber** (PDF text extraction)
- **Groq Python SDK** (`groq`) for LLM scoring
- **python-dotenv** to load environment variables from `.env`

## Project Structure

- `app.py`
  - FastAPI app definition, routes, and Groq integration
  - PDF text extraction helper
  - In-memory leaderboard storage
- `templates/index.html`
  - UI (Tailwind CDN) for uploading resumes and showing results/leaderboard
- `requirements.txt`
  - Python dependencies
- `.env`
  - Local environment variables (should not be committed with real secrets)
- `test.py`
  - Simple HTTP test script (currently appears out-of-date; see notes below)

## Setup

### 1) Create & activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment variables

Create a `.env` file in this `backend` folder:

```env
GROQ_API_KEY=YOUR_GROQ_KEY_HERE
```

Notes:

- **Do not commit** real API keys.
- `app.py` uses `python-dotenv` (`load_dotenv()`) to load `.env` automatically.

## Run the server

From the `backend` directory:

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/`

## How it works (high level)

### PDF text extraction

- Each uploaded PDF is read as bytes (`await f.read()`)
- Text is extracted with `pdfplumber.open(io.BytesIO(file_bytes))`
- Very short/unreadable resumes are skipped (`len(text) < 50`)

### LLM evaluation

- The backend creates a Groq chat completion using:
  - `model="llama-3.3-70b-versatile"`
  - A `SYSTEM_PROMPT` instructing the model to return **strict JSON** with:
    - `score` (0–100)
    - `suggestion`
    - `justification`
    - `edits` (list of strings)
- The Groq call is executed in a thread via `asyncio.to_thread(...)` to avoid blocking the async event loop.

### Leaderboard storage

- Rankings are stored in a **global in-memory list**:
  - `rankings: list[dict] = []`
- This means rankings reset when the server restarts.
- Each entry includes:
  - `id` (short UUID)
  - `filename`
  - `score`, `suggestion`, `justification`, `edits`
  - `rank` (computed when rendering)

## Routes

### `GET /`

- Renders `templates/index.html`
- Sorts `rankings` by `score` descending and assigns `rank` (1..N)

### `POST /evaluate`

- Expects `multipart/form-data`:
  - `job_description` (form field)
  - `files` (one or more PDF files)
- For each valid PDF:
  - extract text
  - call Groq evaluation
  - append results to `results` and global `rankings`
- Returns the same `index.html` template populated with:
  - `results` (only the resumes processed in *this* request)
  - `rankings` (global leaderboard)

Example `curl` (single file):

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -F "job_description=Looking for Senior Python Developer..." \
  -F "files=@resume.pdf"
```

Example `curl` (multiple files):

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -F "job_description=Looking for Senior Python Developer..." \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf"
```

### `POST /clear`

- Clears the in-memory leaderboard (`rankings.clear()`)
- Renders `index.html` again (empty rankings)

## UI (template) notes

- The upload form posts to `POST /evaluate` with `enctype="multipart/form-data"`.
- The file input uses `multiple`, enabling multi-resume uploads.
- The template includes a “Developer API Guide” block with an example `curl`.

## Important notes / inconsistencies to be aware of

- **`.env` currently contains a real-looking API key.** You should rotate it and avoid committing secrets.
- **`test.py` posts to `/evaluate-json`, but that route does not exist in `app.py`.**
  - If you want a JSON API endpoint, you’ll need to add it (or update `test.py` to call `/evaluate` with multipart/form-data).
- `app.py` ends with a comment `# Run with: uvicorn main:app --reload`, but the module file is `app.py`.
  - The correct command is typically `uvicorn app:app --reload`.
- The template’s example `curl` uses `http://localhost:5000/evaluate`, but this FastAPI app commonly runs on port **8000**.
  - Use `http://127.0.0.1:8000/evaluate` unless you explicitly run on `--port 5000`.

## Troubleshooting

- **`GROQ_API_KEY not found` warning**
  - Ensure `.env` exists in `backend/` and contains `GROQ_API_KEY=...`, or set it in your shell environment.

- **No results shown / “No valid PDFs were processed.”**
  - The backend skips:
    - non-PDF files
    - empty uploads
    - PDFs that extract to very little text (`< 50` chars)

- **PDF extraction returns empty text**
  - Some resumes are image/scanned PDFs; `pdfplumber` won’t OCR them.
  - Consider adding OCR (e.g., Tesseract) if needed.

## Security / production notes

- Current leaderboard storage is **in-memory** (global variable). For production, use a database.
- Uploaded files are processed in memory; consider size limits and validation.
- Never commit `.env` with real keys; use secret managers for deployment.
