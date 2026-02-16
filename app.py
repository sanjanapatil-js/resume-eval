import os
import io
import json
import asyncio
import uuid
import pdfplumber
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment variables.")

client = Groq(api_key=GROQ_API_KEY)

# App Configuration
app = FastAPI(title="Resume Evaluator", version="3.0.0")
templates = Jinja2Templates(directory="templates")

# Global storage for this session (In production, use a database)
rankings: list[dict] = []

# Pydantic Model for AI Response
class EvaluationResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    suggestion: str
    justification: str
    edits: list[str] = Field(default_factory=list)

# --- Helper Functions ---

def extract_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for p in pdf.pages:
                extracted = p.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    return text.strip()

SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) and Resume Recruiter.
Compare the Job Description (JD) and the User Resume. 
Calculate a match score (0-100) based on skills, experience, and keywords.

Return response in STRICT JSON format:
{
  "score": 0,
  "suggestion": "Brief advice (max 20 words).",
  "justification": "Why this score? (max 20 words).",
  "edits": ["Specific edit 1", "Specific edit 2", "Specific edit 3"]
}
"""

async def evaluate_resume(jd: str, resume: str) -> EvaluationResponse:
    """Sends prompt to Groq API in a separate thread to keep server async."""
    
    def call_ai():
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Using a valid Groq model
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps({"job_description": jd, "user_resume": resume})},
                ],
                temperature=0.1,  # Low temperature for consistent JSON
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            return EvaluationResponse(**json.loads(content))
        except Exception as e:
            # Fallback in case of AI failure
            print(f"AI Error: {e}")
            return EvaluationResponse(
                score=0, 
                suggestion="AI Service Unavailable", 
                justification="Could not process resume.", 
                edits=[]
            )

    # Run the blocking AI call in a threadpool
    return await asyncio.to_thread(call_ai)


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    # Sort rankings by score before rendering
    sorted_rankings = sorted(rankings, key=lambda x: x["score"], reverse=True)
    # Re-assign ranks
    for i, r in enumerate(sorted_rankings):
        r["rank"] = i + 1
    return templates.TemplateResponse("index.html", {"request": request, "rankings": sorted_rankings})


@app.post("/evaluate", response_class=HTMLResponse)
async def evaluate(
    request: Request, 
    job_description: str = Form(...), 
    files: list[UploadFile] = File(...)
):
    """
    Handle single or multiple PDF uploads.
    'files' argument is a list[UploadFile], which works for 1 or N files.
    """
    results = []

    # Process all files concurrently could be an option, but we'll do sequential for simplicity/rate-limits
    for f in files:
        # 1. Validate File Type
        if not f.filename.lower().endswith(".pdf"):
            continue
        
        # 2. Extract Text
        content = await f.read()
        if not content:
            continue
            
        text = extract_text(content)
        if not text or len(text) < 50:
            # Skip empty or unreadable PDFs
            continue

        # 3. Analyze with AI
        try:
            res = await evaluate_resume(job_description, text)
            
            # 4. Create Result Object
            entry = {
                "id": str(uuid.uuid4())[:8], 
                "filename": f.filename, 
                **res.model_dump()
            }
            
            results.append(entry)
            rankings.append(entry)
        except Exception as e:
            print(f"Skipping {f.filename}: {e}")
            continue

    if not results:
        # You might want to return the page with an error, or just the page
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "results": [], 
            "rankings": rankings,
            "error": "No valid PDFs were processed."
        })

    # Sort Global Rankings
    rankings.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "results": results, 
        "rankings": rankings
    })


@app.post("/clear", response_class=HTMLResponse)
async def clear(request: Request):
    """Clear the leaderboard."""
    rankings.clear()
    return templates.TemplateResponse("index.html", {"request": request, "rankings": rankings})

# Run with: uvicorn main:app --reload