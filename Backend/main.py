import io
import docx
import PyPDF2
import httpx
import json
import os
import base64
import asyncio
import re
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- CONFIGURATION ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found. Please set it in your .env file.")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"

# --- FastAPI App Setup ---
app = FastAPI(
    title="ResumeEnhancer Intelligent API",
    description="An intelligent API using Gemini to analyze resumes and generate updated PDF/LaTeX documents.",
    version="3.8.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FILE PARSING UTILITIES ---
def extract_text_from_docx(file_stream):
    doc = docx.Document(file_stream)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_pdf(file_stream):
    reader = PyPDF2.PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

# --- PYDANTIC MODELS ---
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

class MatchScore(BaseModel):
    score: int = Field(..., description="A numerical score from 0 to 100.")
    reasoning: str = Field(..., description="A brief justification for the score.")

class GeminiAnalysisResponse(BaseModel):
    match_score: MatchScore
    ideal_candidate: IdealCandidate
    resume_feedback: ResumeFeedback
    actionable_suggestions: ActionableSuggestions
    extracted_resume_text: str

class ContactInfo(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None
    location: str | None = None

class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: list[str]

class Education(BaseModel):
    institution: str
    degree: str
    duration: str
    highlights: list[str] | None = None

class Project(BaseModel):
    name: str
    duration: str
    description: list[str]
    link: str | None = None

class Publication(BaseModel):
    title: str
    authors: str
    date: str
    doi: str | None = None

class SkillCategory(BaseModel):
    name: str
    items: list[str]

class StructuredResume(BaseModel):
    contact: ContactInfo
    summary: str | None = None
    experience: list[Experience]
    education: list[Education]
    projects: list[Project] | None = None
    publications: list[Publication] | None = None
    skills: list[SkillCategory]

class GeneratedResume(BaseModel):
    latex_source: str
    pdf_base64: str

# --- GEMINI API HELPER ---
def resolve_refs(schema_part, defs):
    if isinstance(schema_part, dict):
        if "$ref" in schema_part:
            ref_key = schema_part["$ref"].split('/')[-1]
            return resolve_refs(defs.get(ref_key, {}).copy(), defs)
        else:
            return {k: resolve_refs(v, defs) for k, v in schema_part.items()}
    elif isinstance(schema_part, list):
        return [resolve_refs(item, defs) for item in schema_part]
    else:
        return schema_part

async def call_gemini_api(prompt: str, response_schema: BaseModel):
    schema = response_schema.model_json_schema()
    if "$defs" in schema:
        defs = schema.pop("$defs")
        schema = resolve_refs(schema, defs)

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": { "responseMimeType": "application/json", "responseSchema": schema }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload)
            response.raise_for_status()
            response_json = response.json()
            response_text = response_json['candidates'][0]['content']['parts'][0]['text']
            parsed_data = response_schema.model_validate_json(response_text)
            return parsed_data
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API request failed: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the Gemini API: {str(e)}")

# --- CLEANING HELPERS ---
def clean_gemini_output_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = text.replace("C\\#", "C#").replace("C\#", "C#")
    text = text.replace("F\\#", "F#").replace("F\#", "F#")
    text = re.sub(r'\\+', '', text)
    return text

def clean_gemini_recursive(obj):
    if isinstance(obj, str):
        return clean_gemini_output_text(obj)
    elif isinstance(obj, list):
        return [clean_gemini_recursive(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: clean_gemini_recursive(v) for k, v in obj.items()}
    return obj

# --- LATEX ESCAPING ---
def sanitize_latex(text: str | None) -> str:
    if text is None:
        return ""
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('#', r'\#'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
        ('|', r'\textbar{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def escape_latex_recursive(obj):
    if isinstance(obj, str):
        return sanitize_latex(obj)
    elif isinstance(obj, list):
        return [escape_latex_recursive(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: escape_latex_recursive(v) for k, v in obj.items()}
    else:
        return obj

# --- NEW ACADEMIC CV-STYLE BUILDER ---
def build_latex_resume(data: StructuredResume) -> str:
    def esc(s: str | None) -> str:
        return sanitize_latex(s) if s else ""
    
    # Build contact header
    contact_parts = []
    if data.contact.location:
        contact_parts.append(f"\\mbox{{{esc(data.contact.location)}}}")
    if data.contact.email:
        contact_parts.append(f"\\mbox{{\\hrefWithoutArrow{{mailto:{esc(data.contact.email)}}}{{{esc(data.contact.email)}}}}}")
    if data.contact.phone:
        contact_parts.append(f"\\mbox{{\\hrefWithoutArrow{{tel:{esc(data.contact.phone)}}}{{{esc(data.contact.phone)}}}}}")
    if data.contact.website:
        contact_parts.append(f"\\mbox{{\\hrefWithoutArrow{{{esc(data.contact.website)}}}{{{esc(data.contact.website)}}}}}")
    if data.contact.linkedin:
        linkedin_short = data.contact.linkedin.replace("https://", "").replace("www.", "")
        contact_parts.append(f"\\mbox{{\\hrefWithoutArrow{{{esc(data.contact.linkedin)}}}{{{esc(linkedin_short)}}}}}")
    if data.contact.github:
        github_short = data.contact.github.replace("https://", "").replace("www.", "")
        contact_parts.append(f"\\mbox{{\\hrefWithoutArrow{{{esc(data.contact.github)}}}{{{esc(github_short)}}}}}")
    
    contact_str = "\n".join([
        f"        {part}%\n        \\kern 5.0 pt%\n        \\AND%\n        \\kern 5.0 pt%"
        for part in contact_parts
    ])
    
    # Build sections
    sections = []
    
    # Summary section
    if data.summary:
        sections.append(f"""
\\section{{Summary}}

\\begin{{onecolentry}}
    {esc(data.summary)}
\\end{{onecolentry}}
""")
    
    # Education section
    if data.education:
        edu_items = []
        for edu in data.education:
            highlights = ""
            if edu.highlights:
                highlights = "\\begin{highlights}\n" + "\n".join([
                    f"    \\item {esc(item)}" for item in edu.highlights
                ]) + "\n\\end{highlights}"
            
            edu_items.append(f"""
\\begin{{twocolentry}}{{
    {esc(edu.duration)}
}}
    \\textbf{{{esc(edu.institution)}}}, {esc(edu.degree)}
\\end{{twocolentry}}
{highlights}
""")
        
        sections.append(f"""
\\section{{Education}}

{"".join(edu_items)}
""")
    
    # Experience section
    if data.experience:
        exp_items = []
        for exp in data.experience:
            description = "\\begin{highlights}\n" + "\n".join([
                f"    \\item {esc(item)}" for item in exp.description
            ]) + "\n\\end{highlights}"
            
            exp_items.append(f"""
\\begin{{twocolentry}}{{
    {esc(exp.duration)}
}}
    \\textbf{{{esc(exp.company)}}}, {esc(exp.role)}
\\end{{twocolentry}}
\\begin{{onecolentry}}
{description}
\\end{{onecolentry}}
""")
        
        sections.append(f"""
\\section{{Experience}}

{"".join(exp_items)}
""")
    
    # Projects section
    if data.projects:
        proj_items = []
        for proj in data.projects:
            description = "\\begin{highlights}\n" + "\n".join([
                f"    \\item {esc(item)}" for item in proj.description
            ]) + "\n\\end{highlights}"
            
            link = proj.link if proj.link else ""
            proj_items.append(f"""
\\begin{{twocolentry}}{{
    {esc(link)}
}}
    \\textbf{{{esc(proj.name)}}}
\\end{{twocolentry}}
\\begin{{onecolentry}}
{description}
\\end{{onecolentry}}
""")
        
        sections.append(f"""
\\section{{Projects}}

{"".join(proj_items)}
""")
    
    # Publications section
    if data.publications:
        pub_items = []
        for pub in data.publications:
            doi_link = f"\\href{{{esc(pub.doi)}}}{{{esc(pub.doi)}}}" if pub.doi else ""
            pub_items.append(f"""
\\begin{{twocolentry}}{{
    {esc(pub.date)}
}}
    \\textbf{{{esc(pub.title)}}}
\\end{{twocolentry}}
\\begin{{onecolentry}}
    {esc(pub.authors)}
    \\vspace{{0.10 cm}}
    {doi_link}
\\end{{onecolentry}}
""")
        
        sections.append(f"""
\\section{{Publications}}

{"".join(pub_items)}
""")
    
    # Skills section
    if data.skills:
        skill_items = []
        for skill_cat in data.skills:
            items = ", ".join([esc(item) for item in skill_cat.items])
            skill_items.append(f"""
\\begin{{onecolentry}}
    \\textbf{{{esc(skill_cat.name)}}}: {items}
\\end{{onecolentry}}
""")
        
        sections.append(f"""
\\section{{Skills}}

{"".join(skill_items)}
""")
    
    # Combine all parts
    latex_template = f"""\\documentclass[10pt, letterpaper]{{article}}

% Packages:
\\usepackage[
    ignoreheadfoot, % set margins without considering header and footer
    top=0.2in, % seperation between body and page edge from the top
    bottom=0.2in, % seperation between body and page edge from the bottom
    left=0.2in, % seperation between body and page edge from the left
    right=0.2in, % seperation between body and page edge from the right
    footskip=0.2in, % seperation between body and footer
    % showframe % for debugging 
]{{geometry}} % for adjusting page geometry
\\usepackage{{titlesec}} % for customizing section titles
\\usepackage{{tabularx}} % for making tables with fixed width columns
\\usepackage{{array}} % tabularx requires this
\\usepackage[dvipsnames]{{xcolor}} % for coloring text
\\definecolor{{primaryColor}}{{RGB}}{{0, 0, 0}} % define primary color
\\usepackage{{enumitem}} % for customizing lists
\\usepackage{{fontawesome5}} % for using icons
\\usepackage{{amsmath}} % for math
\\usepackage[
    pdftitle={{{esc(data.contact.name)}'s CV}},
    pdfauthor={{{esc(data.contact.name)}}},
    pdfcreator={{LaTeX with RenderCV}},
    colorlinks=true,
    urlcolor=primaryColor
]{{hyperref}} % for links, metadata and bookmarks
\\usepackage[pscoord]{{eso-pic}} % for floating text on the page
\\usepackage{{calc}} % for calculating lengths
\\usepackage{{bookmark}} % for bookmarks
\\usepackage{{lastpage}} % for getting the total number of pages
\\usepackage{{changepage}} % for one column entries (adjustwidth environment)
\\usepackage{{paracol}} % for two and three column entries
\\usepackage{{ifthen}} % for conditional statements
\\usepackage{{needspace}} % for avoiding page brake right after the section title
\\usepackage{{iftex}} % check if engine is pdflatex, xetex or luatex

% Ensure that generate pdf is machine readable/ATS parsable:
\\ifPDFTeX
    \\input{{glyphtounicode}}
    \\pdfgentounicode=1
    \\usepackage[T1]{{fontenc}}
    \\usepackage[utf8]{{inputenc}}
    \\usepackage{{lmodern}}
\\fi

\\usepackage{{charter}}

% Some settings:
\\raggedright
\\AtBeginEnvironment{{adjustwidth}}{{\\partopsep0pt}} % remove space before adjustwidth environment
\\pagestyle{{empty}} % no header or footer
\\setcounter{{secnumdepth}}{{0}} % no section numbering
\\setlength{{\\parindent}}{{0pt}} % no indentation
\\setlength{{\\topskip}}{{0pt}} % no top skip
\\setlength{{\\columnsep}}{{0.15cm}} % set column seperation
\\pagenumbering{{gobble}} % no page numbering

\\titleformat{{\\section}}{{\\needspace{{4\\baselineskip}}\\bfseries\\large}}{{}}{{0pt}}{{}}[\\vspace{{1pt}}\\titlerule]

\\titlespacing{{\\section}}{{
    % left space:
    -1pt
}}{{
    % top space:
    0.2 cm
}}{{
    % bottom space:
    0.2 cm
}} % section title spacing

\\renewcommand\\labelitemi{{$\\vcenter{{\\hbox{{\\small$\\bullet$}}}}$}} % custom bullet points
\\newenvironment{{highlights}}{{
    \\begin{{itemize}}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=0 cm + 10pt
    ]
}}{{
    \\end{{itemize}}
}} % new environment for highlights

\\newenvironment{{highlightsforbulletentries}}{{
    \\begin{{itemize}}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=10pt
    ]
}}{{
    \\end{{itemize}}
}} % new environment for highlights for bullet entries

\\newenvironment{{onecolentry}}{{
    \\begin{{adjustwidth}}{{
        0 cm + 0.00001 cm
    }}{{
        0 cm + 0.00001 cm
    }}
}}{{
    \\end{{adjustwidth}}
}} % new environment for one column entries

\\newenvironment{{twocolentry}}[2][]{{
    \\onecolentry
    \\def\\secondColumn{{#2}}
    \\setcolumnwidth{{\\fill, 4.5 cm}}
    \\begin{{paracol}}{{2}}
}}{{
    \\switchcolumn \\raggedleft \\secondColumn
    \\end{{paracol}}
    \\endonecolentry
}} % new environment for two column entries

\\newenvironment{{threecolentry}}[3][]{{
    \\onecolentry
    \\def\\thirdColumn{{#3}}
    \\setcolumnwidth{{, \\fill, 4.5 cm}}
    \\begin{{paracol}}{{3}}
    {{\\raggedright #2}} \\switchcolumn
}}{{
    \\switchcolumn \\raggedleft \\thirdColumn
    \\end{{paracol}}
    \\endonecolentry
}} % new environment for three column entries

\\newenvironment{{header}}{{
    \\setlength{{\\topsep}}{{0pt}}\\par\\kern\\topsep\\centering\\linespread{{1.5}}
}}{{
    \\par\\kern\\topsep
}} % new environment for the header

% save the original href command in a new command:
\\let\\hrefWithoutArrow\\href

% Define AND separator
\\newcommand{{\\AND}}{{\\unskip
    \\cleaders\\copy\\ANDbox\\hskip\\wd\\ANDbox
    \\ignorespaces
}}
\\newsavebox\\ANDbox
\\sbox\\ANDbox{{$|$}}

\\begin{{document}}
    \\begin{{header}}
        \\fontsize{{25 pt}}{{25 pt}}\\selectfont {esc(data.contact.name)}
        
        \\vspace{{5 pt}}
        
        \\normalsize
{contact_str}
    \\end{{header}}
    
    \\vspace{{5 pt - 0.3 cm}}
    
{"".join(sections)}
\\end{{document}}
"""
    return latex_template

# --- API ENDPOINTS ---
@app.post("/gemini-analyze", response_model=GeminiAnalysisResponse)
async def gemini_analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        file_stream = io.BytesIO(await resume.read())
        if resume.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_stream)
        elif resume.filename.endswith('.docx'):
            resume_text = extract_text_from_docx(file_stream)
        elif resume.filename.endswith('.txt'):
            resume_text = file_stream.read().decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Invalid file type.")
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the resume.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading or parsing the resume file: {str(e)}")

    ideal_candidate_response = await call_gemini_api(f"As an expert technical recruiter, analyze the following job description and create a profile of the ideal candidate.\n\n{job_description}", IdealCandidate)
    resume_feedback_response = await call_gemini_api(f"Compare the provided resume against the ideal candidate profile and the job description.\n\nResume:\n{resume_text}", ResumeFeedback)
    match_score_response = await call_gemini_api(f"Assign a numerical match score from 0 to 100 and give a short justification.\n\nResume:\n{resume_text}", MatchScore)
    actionable_suggestions_response = await call_gemini_api(f"Generate 3-4 specific, action-oriented bullet points that the user can add to their resume to address the gaps.\n\nResume:\n{resume_text}", ActionableSuggestions)

    return GeminiAnalysisResponse(
        match_score=match_score_response,
        ideal_candidate=ideal_candidate_response,
        resume_feedback=resume_feedback_response,
        actionable_suggestions=actionable_suggestions_response,
        extracted_resume_text=resume_text
    )

@app.post("/generate-resume", response_model=GeneratedResume)
async def generate_resume_endpoint(
    resume_text: str = Form(...),
    suggestions: str = Form(...)
):
    parsing_prompt = f"""
You are an expert technical resume parser. Parse this resume into StructuredResume JSON and integrate these suggestions:
{suggestions}

Resume:
{resume_text}
"""
    structured_resume_data = await call_gemini_api(parsing_prompt, StructuredResume)

    structured_resume_data = clean_gemini_recursive(structured_resume_data.model_dump())
    structured_resume_data = escape_latex_recursive(structured_resume_data)
    structured_resume_data = StructuredResume(**structured_resume_data)

    try:
        latex_source = build_latex_resume(structured_resume_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build LaTeX document: {str(e)}")

    try:
        temp_tex = f"resume_output_{os.urandom(8).hex()}.tex"
        with open(temp_tex, "w", encoding="utf-8") as f:
            f.write(latex_source)

        os.system(f"pdflatex -interaction=nonstopmode {temp_tex}")
        pdf_path = temp_tex.replace(".tex", ".pdf")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError("PDF file was not generated by LaTeX.")

        with open(pdf_path, "rb") as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        for ext in (".aux", ".log", ".out", ".pdf", ".tex"):
            try:
                os.remove(temp_tex.replace(".tex", ext))
            except FileNotFoundError:
                pass

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
        
    return GeneratedResume(latex_source=latex_source, pdf_base64=pdf_base64)