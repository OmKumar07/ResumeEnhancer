import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, BrainCircuit, CheckCircle, XCircle, Loader, ArrowRight, UserCheck, BarChart, Sparkles, ClipboardCopy, FileDown, Code } from 'lucide-react';

// Helper component for displaying each section of the report
const ReportSection = ({ icon, title, children }) => (
  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
    <div className="flex items-center gap-3 mb-4">
      {icon}
      <h3 className="text-xl font-bold text-slate-800">{title}</h3>
    </div>
    <div className="space-y-3 text-slate-600">
      {children}
    </div>
  </div>
);

// Main App Component
const App = () => {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // NEW: State for the resume generation feature
  const [generatedResume, setGeneratedResume] = useState(null);
  const [isGeneratingResume, setIsGeneratingResume] = useState(false);
  const [resumeError, setResumeError] = useState('');
  const [copiedStatus, setCopiedStatus] = useState(''); // To show 'Copied!' message

  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const handleInitialAnalysis = async (e) => {
    e.preventDefault();
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload a resume and paste a job description.');
      return;
    }
    setIsLoading(true);
    setError('');
    setAnalysisResult(null);
    setGeneratedResume(null); // Reset resume on new analysis

    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('job_description', jobDescription);

    try {
      const response = await axios.post('http://127.0.0.1:8000/gemini-analyze', formData);
      setAnalysisResult(response.data);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'An unexpected error occurred during analysis.';
      setError(`Analysis failed: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // NEW: Function to handle the final resume generation
  const handleGenerateResume = async () => {
    if (!analysisResult) return;

    setIsGeneratingResume(true);
    setResumeError('');
    
    const formData = new FormData();
    formData.append('resume_text', analysisResult.extracted_resume_text);
    formData.append('suggestions', JSON.stringify(analysisResult.actionable_suggestions.bullet_points));

    try {
        const response = await axios.post('http://127.0.0.1:8000/generate-resume', formData);
        setGeneratedResume(response.data);
    } catch (err) {
        const errorMessage = err.response?.data?.detail || 'An unexpected error occurred during resume generation.';
        setResumeError(`Generation failed: ${errorMessage}`);
    } finally {
        setIsGeneratingResume(false);
    }
  };
  
  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text).then(() => {
        setCopiedStatus(type);
        setTimeout(() => setCopiedStatus(''), 2000);
    });
  };

  return (
    <div className="bg-slate-50 min-h-screen font-sans text-slate-800">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8">
        
        <header className="text-center mb-10">
            <div className="inline-flex items-center gap-3">
                <BrainCircuit className="w-10 h-10 text-indigo-600" />
                <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Resume<span className="text-indigo-600">Enhancer</span></h1>
            </div>
            <p className="mt-3 text-lg text-slate-600 max-w-2xl mx-auto">From analysis to professionally formatted PDF, all powered by AI.</p>
        </header>

        <main>
          {/* Form Section */}
          <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
            <form onSubmit={handleInitialAnalysis}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <label htmlFor="resume-upload" className="block text-lg font-semibold mb-2 flex items-center gap-2"><Upload className="w-5 h-5" /> Upload Resume</label>
                  <div className="relative border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors">
                    <input type="file" id="resume-upload" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={handleFileChange} accept=".pdf,.docx,.txt" />
                    <div className="flex flex-col items-center justify-center h-full"><FileText className="w-10 h-10 text-slate-400 mb-2" />{resumeFile ? <p className="text-slate-700 font-medium">{resumeFile.name}</p> : <p className="text-slate-500">Click to upload</p>}<p className="text-xs text-slate-400 mt-1">PDF, DOCX, or TXT</p></div>
                  </div>
                </div>
                <div>
                  <label htmlFor="job-description" className="block text-lg font-semibold mb-2 flex items-center gap-2"><FileText className="w-5 h-5" /> Job Description</label>
                  <textarea id="job-description" rows="8" className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition" placeholder="Paste the full job description or just a title..." value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} />
                </div>
              </div>
              <div className="mt-8 text-center"><button type="submit" className="bg-indigo-600 text-white font-bold text-lg py-3 px-8 rounded-lg hover:bg-indigo-700 disabled:bg-slate-400 flex items-center justify-center gap-3 mx-auto" disabled={isLoading}>{isLoading ? <><Loader className="animate-spin w-6 h-6" /> Analyzing...</> : <>Generate Analysis <ArrowRight className="w-6 h-6" /></>}</button></div>
            </form>
          </div>

          {isLoading && <div className="text-center mt-8"><p className="text-lg text-slate-600">AI is analyzing... this may take up to 45 seconds.</p></div>}
          {error && <div className="max-w-4xl mx-auto mt-8 p-4 bg-red-100 text-red-800 border border-red-300 rounded-lg text-center">{error}</div>}

          {/* Analysis Report Section */}
          {analysisResult && (
            <div className="max-w-4xl mx-auto mt-10 space-y-8 animate-fade-in">
              <h2 className="text-3xl font-bold text-center">Your AI-Powered Report</h2>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm text-center">
                <h3 className="text-xl font-bold text-slate-800 mb-4">Overall Match Score</h3>
                <div className="flex justify-center items-center"><div className="relative w-48 h-48"><svg className="w-full h-full" viewBox="0 0 36 36"><path className="text-slate-200" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" /><path className="text-indigo-600" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray={`${analysisResult.match_score.score}, 100`} /></svg><div className="absolute inset-0 flex flex-col items-center justify-center"><span className="text-5xl font-bold text-indigo-600">{analysisResult.match_score.score}</span><span className="text-lg text-slate-600">out of 100</span></div></div></div>
                <p className="mt-4 text-slate-600 max-w-lg mx-auto italic">"{analysisResult.match_score.reasoning}"</p>
              </div>
              
              <ReportSection icon={<UserCheck className="w-7 h-7 text-blue-500" />} title="Ideal Candidate Profile">
                <p>{analysisResult.ideal_candidate.summary}</p>
                <div className="pt-2">
                  <h4 className="font-semibold text-slate-700">Key Technologies:</h4>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {analysisResult.ideal_candidate.key_technologies.map((tech, i) => <span key={i} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">{tech}</span>)}
                  </div>
                </div>
              </ReportSection>

              <ReportSection icon={<BarChart className="w-7 h-7 text-amber-500" />} title="Your Resume Analysis">
                <p className="italic">"{analysisResult.resume_feedback.suggestion_summary}"</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div>
                        <h4 className="font-semibold text-slate-700 flex items-center gap-2"><CheckCircle className="text-green-500"/> Strengths</h4>
                        <ul className="list-disc list-inside mt-1">{analysisResult.resume_feedback.strengths.map((item, i) => <li key={i}>{item}</li>)}</ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-slate-700 flex items-center gap-2"><XCircle className="text-red-500"/> Areas for Improvement</h4>
                        <ul className="list-disc list-inside mt-1">{analysisResult.resume_feedback.areas_for_improvement.map((item, i) => <li key={i}>{item}</li>)}</ul>
                    </div>
                </div>
              </ReportSection>

              <ReportSection icon={<Sparkles className="w-7 h-7 text-fuchsia-500" />} title="Actionable Suggestions">
                 <p>Copy these AI-generated bullet points and add them to your resume to address the gaps.</p>
                 <div className="space-y-3 pt-2">
                  {analysisResult.actionable_suggestions.bullet_points.map((point, i) => (
                    <div key={i} className="bg-slate-100 p-3 rounded-lg flex items-start justify-between gap-4 border border-slate-200">
                      <p className="flex-grow">{point}</p>
                      <button onClick={() => copyToClipboard(point, 'suggestion')} className="text-slate-500 hover:text-indigo-600 transition-colors p-1 rounded-md flex-shrink-0">
                        {copiedStatus === 'suggestion' ? <CheckCircle className="w-5 h-5 text-green-600" /> : <ClipboardCopy className="w-5 h-5" />}
                      </button>
                    </div>
                  ))}
                </div>
              </ReportSection>
              
              {/* NEW: Resume Generation Section */}
              <div className="mt-10 pt-8 border-t border-slate-200 text-center">
                <h3 className="text-2xl font-bold mb-4">Generate Your Enhanced Resume</h3>
                <p className="text-slate-600 mb-6 max-w-2xl mx-auto">Ready to see the final product? Let AI build a professionally formatted PDF with all the suggested improvements integrated.</p>
                <button onClick={handleGenerateResume} disabled={isGeneratingResume} className="bg-green-600 text-white font-bold text-lg py-3 px-8 rounded-lg hover:bg-green-700 disabled:bg-slate-400 flex items-center justify-center gap-3 mx-auto">
                  {isGeneratingResume ? <><Loader className="animate-spin w-6 h-6" /> Generating PDF...</> : <>Generate Resume <FileDown className="w-6 h-6" /></>}
                </button>
              </div>

              {resumeError && <div className="mt-4 p-3 bg-red-100 text-red-800 border border-red-300 rounded-lg text-center">{resumeError}</div>}
              
              {generatedResume && (
                <div className="mt-8 animate-fade-in">
                    <h3 className="text-2xl font-bold text-center mb-6">Your New Resume is Ready!</h3>
                    <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200 shadow-lg">
                        <div className="bg-slate-800 p-2 rounded-t-lg flex justify-end gap-4">
                            <a href={`data:application/pdf;base64,${generatedResume.pdf_base64}`} download="Enhanced_Resume.pdf" className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md flex items-center gap-2">
                                <FileDown className="w-4 h-4" /> Download PDF
                            </a>
                            <button onClick={() => copyToClipboard(generatedResume.latex_source, 'latex')} className="px-4 py-2 text-sm font-semibold text-white bg-gray-600 hover:bg-gray-700 rounded-md flex items-center gap-2">
                                {copiedStatus === 'latex' ? <><CheckCircle className="w-4 h-4" /> Copied!</> : <><Code className="w-4 h-4" /> Copy LaTeX Code</>}
                            </button>
                        </div>
                        <div className="w-full h-[600px] sm:h-[800px] bg-slate-100">
                            <embed src={`data:application/pdf;base64,${generatedResume.pdf_base64}`} type="application/pdf" width="100%" height="100%" />
                        </div>
                    </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
