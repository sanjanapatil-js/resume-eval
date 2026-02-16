

# Resume Evaluator — Backend (FastAPI)

> **Built for Entrata Assignment** by Sanjana  
> 🔗 **Live Demo:** [https://sanjanajsx-resume-eval.hf.space](https://sanjanajsx-resume-eval.hf.space)

---

## What is this?

A simple web app that takes a **Job Description** + **PDF resumes**, runs them through **Groq's LLM**, and gives each resume an ATS-style score (0–100) with feedback. There's also a leaderboard to compare multiple resumes side by side.

---

## How I built it

- **FastAPI** for the backend
- **pdfplumber** to extract text from uploaded PDFs
- **Groq API** (LLaMA 3.3 70B) to score and evaluate resumes against the JD
- **Jinja2 + Tailwind CSS** for a simple server-rendered UI
- Deployed on **Hugging Face Spaces**

---

## Folder Structure

```
backend/
├── app.py                 # Main FastAPI app (routes, PDF extraction, Groq calls)
├── templates/
│   └── index.html         # Frontend UI (Tailwind CDN)
├── requirements.txt       # Python dependencies
├── .env                   # GROQ_API_KEY (don't commit real keys)
└── test.py                # Quick test script
```

---

## Try it out (Live)

Just open the live link — no setup needed:

**[https://sanjanajsx-resume-eval.hf.space](https://sanjanajsx-resume-eval.hf.space)**

Or test via `curl`:

```bash
# Single resume
curl -X POST https://sanjanajsx-resume-eval.hf.space/evaluate \
  -F "job_description=Looking for a Senior Python Developer..." \
  -F "files=@resume.pdf"

# Multiple resumes
curl -X POST https://sanjanajsx-resume-eval.hf.space/evaluate \
  -F "job_description=Looking for a Senior Python Developer..." \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.pdf"
```

---

## Run it locally

**1. Clone & go to backend folder**

```bash
cd backend
```

**2. Create a virtual environment & install deps**

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .\.venv\Scripts\Activate.ps1   # Windows PowerShell

pip install -r requirements.txt
```

**3. Add your Groq API key**

Create a `.env` file inside `backend/`:

```env
GROQ_API_KEY=your_key_here
```

**4. Start the server**

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) — upload a JD and resumes, hit evaluate.

---

## How it works

1. You paste a **Job Description** and upload **one or more PDF resumes**
2. Backend extracts text from each PDF using **pdfplumber**
3. Sends the JD + resume text to **Groq LLM** which returns:
   - **Score** (0–100)
   - **Suggestion** — what to improve
   - **Justification** — why this score
   - **Edits** — specific changes to make
4. Results are shown on screen and added to an **in-memory leaderboard**

---

## Routes

| Method | Path | What it does |
|--------|------|-------------|
| `GET` | `/` | Renders the UI with current leaderboard |
| `POST` | `/evaluate` | Accepts JD + PDFs, returns scores |
| `POST` | `/clear` | Clears the leaderboard |

---

## Good to know

- **Leaderboard resets** on server restart (it's in-memory, not a database)
- **Scanned/image PDFs** won't work — pdfplumber can't OCR them
- PDFs with very little extractable text (< 50 chars) are skipped
- Don't commit `.env` with real API keys

---
