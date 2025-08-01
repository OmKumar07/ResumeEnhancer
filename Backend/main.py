# main.py
import io
import docx
import PyPDF2
import spacy

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# --- METADATA & CORS ---

# Description for the API documentation
description = """
ResumeEnhancer API helps you analyze your resume against a job description.

You can:
- Calculate a match score.
- Identify keywords that match.
- Find keywords that are missing from your resume.
"""

# Initialize the FastAPI app
app = FastAPI(
    title="ResumeEnhancer API",
    description=description,
    version="1.0.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your frontend (running on a different domain/port) to communicate with this backend.
origins = [
    "http://localhost:3000",  # The default address for React development server
    "http://localhost:8080",
    # Add other frontend origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Load the spaCy English model
# We use 'en_core_web_sm' for its efficiency.
nlp = spacy.load("en_core_web_sm")


# --- UTILITY FUNCTIONS ---

def extract_text_from_docx(file_stream):
    """Extracts text from a DOCX file."""
    doc = docx.Document(file_stream)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file."""
    reader = PyPDF2.PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def preprocess_text(text):
    """
    Cleans and preprocesses the text:
    1. Removes punctuation and special characters.
    2. Converts to lowercase.
    3. Lemmatizes words (e.g., 'running' -> 'run').
    4. Removes common stop words.
    """
    # Remove punctuation and non-alphanumeric characters
    text = re.sub(r'[^\w\s]', '', text)
    doc = nlp(text.lower())
    
    tokens = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and token.is_alpha
    ]
    return " ".join(tokens)


# --- PYDANTIC MODELS (for Request/Response structure) ---

class AnalysisResult(BaseModel):
    """Defines the structure of the analysis result returned by the API."""
    match_score: float
    matched_keywords: list[str]
    missing_keywords: list[str]


# --- API ENDPOINT ---

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_resume(
    resume: UploadFile = File(..., description="The user's resume file (PDF or DOCX)."),
    job_description: str = Form(..., description="The job description text.")
):
    """
    Analyzes a resume against a job description and returns a match score
    and keyword analysis.
    """
    # 1. Validate file type
    if not resume.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF or DOCX file.")

    # 2. Extract text from the uploaded resume
    try:
        file_stream = io.BytesIO(await resume.read())
        if resume.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_stream)
        else: # .docx
            resume_text = extract_text_from_docx(file_stream)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    # 3. Preprocess both the resume and job description text
    processed_resume = preprocess_text(resume_text)
    processed_jd = preprocess_text(job_description)

    # 4. Vectorize text using TF-IDF
    # TF-IDF (Term Frequency-Inverse Document Frequency) converts text into numerical
    # vectors, giving more weight to words that are important to a document.
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([processed_resume, processed_jd])

    # 5. Calculate Cosine Similarity
    # This measures the cosine of the angle between the two vectors, giving a score
    # from 0 (not similar) to 1 (identical).
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    match_score = round(cosine_sim[0][0] * 100, 2)

    # 6. Keyword Analysis
    jd_vectorizer = TfidfVectorizer().fit(preprocess_text(t) for t in [job_description])
    jd_keywords = set(jd_vectorizer.get_feature_names_out())
    
    resume_vectorizer = TfidfVectorizer().fit(preprocess_text(t) for t in [resume_text])
    resume_keywords = set(resume_vectorizer.get_feature_names_out())

    # Find matched and missing keywords
    matched_keywords = list(jd_keywords.intersection(resume_keywords))
    missing_keywords = list(jd_keywords.difference(resume_keywords))

    return AnalysisResult(
        match_score=match_score,
        matched_keywords=sorted(matched_keywords),
        missing_keywords=sorted(missing_keywords)
    )

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"message": "Welcome to the ResumeEnhancer API! Go to /docs for the documentation."}
# Add this import at the top of your file with the others
import os 

# --- NEW GEMINI-POWERED ANALYSIS SECTION ---

class GeminiAnalysisRequest(BaseModel):
    """Defines the structure for the new analysis request."""
    resume_text: str
    job_description: str

class IdealCandidate(BaseModel):
    """Defines the structure for the ideal candidate profile."""
    summary: str
    key_skills: list[str]
    key_technologies: list[str]
    experience_level: str

# This is a placeholder for now. We will build this out.
class FullAnalysis(BaseModel):
    ideal_candidate: IdealCandidate
    # We will add more fields here later, like strengths, weaknesses, etc.


@app.post("/gemini-analyze", response_model=IdealCandidate)
async def gemini_analyze_resume(request: GeminiAnalysisRequest):
    """
    Performs an intelligent analysis using the Gemini API.
    
    Step 1: Creates a profile of the ideal candidate based on the job description.
    (Future steps will compare the resume against this profile).
    """
    
    # --- Step 1: Create Ideal Candidate Profile ---
    
    # This prompt asks Gemini to act as an expert recruiter.
    ideal_candidate_prompt = f"""
    As an expert technical recruiter, analyze the following job description and create a profile of the ideal candidate. 
    Identify the most important skills, technologies, and the required level of experience.

    **Job Description:**
    ---
    {request.job_description}
    ---
    """

    try:
        # This is where you would make the actual call to the Gemini API
        # For now, we will return a hardcoded example to test the structure.
        
        # In the next step, we will replace this with a real API call.
        print("--- PROMPT FOR IDEAL CANDIDATE ---")
        print(ideal_candidate_prompt)
        print("---------------------------------")

        # --- MOCK RESPONSE (Example of what Gemini would return) ---
        mock_ideal_candidate = IdealCandidate(
            summary="The ideal candidate is a mid-to-senior level Web Developer with strong proficiency in modern frontend frameworks like React and backend experience with Node.js. They should be skilled in building and consuming RESTful APIs and have a solid understanding of database management.",
            key_skills=["API Design", "Agile Methodologies", "Problem Solving", "UI/UX Principles"],
            key_technologies=["React", "Node.js", "Express", "PostgreSQL", "Tailwind CSS", "Docker"],
            experience_level="3-5 years"
        )

        return mock_ideal_candidate

    except Exception as e:
        # This will handle errors if the API call fails in the future
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")