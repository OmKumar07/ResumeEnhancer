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