import io
import docx
import PyPDF2
import httpx 
import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

# --- CONFIGURATION ---
load_dotenv() 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found. Please set it in your .env file.")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

# --- FastAPI App Setup ---
app = FastAPI(
    title="ResumeEnhancer Intelligent API",
    description="An intelligent API using Gemini to analyze resumes against job descriptions.",
    version="2.1.0", # Version bump for the fix
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UTILITY FUNCTIONS FOR FILE PARSING ---
def extract_text_from_docx(file_stream):
    """Extracts text from a DOCX file stream."""
    doc = docx.Document(file_stream)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file stream."""
    reader = PyPDF2.PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

# --- PYDANTIC MODELS (Data Structures) ---
class IdealCandidate(BaseModel):
    summary: str
    key_skills: list[str]
    key_technologies: list[str]
    experience_level: str

class ResumeFeedback(BaseModel):
    strengths: list[str]
    areas_for_improvement: list[str]
    suggestion_summary: str

class ActionableSuggestions(BaseModel):
    bullet_points: list[str]

class GeminiAnalysisResponse(BaseModel):
    ideal_candidate: IdealCandidate
    resume_feedback: ResumeFeedback
    actionable_suggestions: ActionableSuggestions

# --- GEMINI API HELPER FUNCTION ---
async def call_gemini_api(prompt: str, response_schema: BaseModel):
    """Calls the Gemini API and validates the response against a Pydantic schema."""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema.model_json_schema()
        }
    }
    # Increased timeout for potentially long Gemini responses
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload)
            response.raise_for_status()
            response_json = response.json()
            response_text = response_json['candidates'][0]['content']['parts'][0]['text']
            parsed_data = response_schema.model_validate_json(response_text)
            return parsed_data
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API request failed: {e.response.text}")
        except (ValidationError, KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing or validating Gemini response: {e}")
            raise HTTPException(status_code=500, detail="Failed to process response from Gemini API.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while contacting the Gemini API.")

# --- CORRECTED API ENDPOINT ---
@app.post("/gemini-analyze", response_model=GeminiAnalysisResponse)
async def gemini_analyze_resume(
    resume: UploadFile = File(..., description="The user's resume file (PDF, DOCX, or TXT)."),
    job_description: str = Form(..., description="The job description text or title.")
):
    """
    Performs an intelligent, multi-step analysis using the Gemini API.
    This endpoint now correctly handles file uploads and parsing on the backend.
    """
    # Step 1: Extract text from the uploaded resume file
    try:
        file_stream = io.BytesIO(await resume.read())
        if resume.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_stream)
        elif resume.filename.endswith('.docx'):
            resume_text = extract_text_from_docx(file_stream)
        elif resume.filename.endswith('.txt'):
             resume_text = file_stream.read().decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF, DOCX, or TXT file.")
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the resume. The file might be empty, image-based, or corrupted.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading or parsing the resume file: {str(e)}")

    # Step 2: Create Ideal Candidate Profile
    ideal_candidate_prompt = f"As an expert technical recruiter, analyze the following job description and create a profile of the ideal candidate.\n\n**Job Description:**\n---\n{job_description}\n---"
    ideal_candidate_response = await call_gemini_api(ideal_candidate_prompt, IdealCandidate)

    # Step 3: Analyze Resume Against the Ideal Profile
    resume_analysis_prompt = f"""You are an expert career coach. Compare the provided resume against the ideal candidate profile and the original job description. Provide constructive feedback.\n\n**Ideal Candidate Profile:**\n---\n{ideal_candidate_response.model_dump_json(indent=2)}\n---\n\n**Original Job Description:**\n---\n{job_description}\n---\n\n**User's Resume:**\n---\n{resume_text}\n---"""
    resume_feedback_response = await call_gemini_api(resume_analysis_prompt, ResumeFeedback)

    # Step 4: Generate Actionable Suggestions
    suggestion_generation_prompt = f"""You are an expert resume writer. Based on the previous analysis (strengths, weaknesses, and job description), generate 3-4 specific, action-oriented bullet points that the user can add to their resume. The bullet points should be impactful and use professional language.\n\n**Analysis Context:**\n---\nIdeal Candidate: {ideal_candidate_response.summary}\nCandidate's Strengths: {', '.join(resume_feedback_response.strengths)}\nCandidate's Weaknesses: {', '.join(resume_feedback_response.areas_for_improvement)}\n---\n\n**User's Resume:**\n---\n{resume_text}\n---"""
    actionable_suggestions_response = await call_gemini_api(suggestion_generation_prompt, ActionableSuggestions)

    # Final Step: Combine and Return the Full Analysis
    return GeminiAnalysisResponse(
        ideal_candidate=ideal_candidate_response,
        resume_feedback=resume_feedback_response,
        actionable_suggestions=actionable_suggestions_response,
    )
