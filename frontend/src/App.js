import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, BrainCircuit, CheckCircle, XCircle, Loader, ArrowRight, UserCheck, BarChart, Sparkles, ClipboardCopy } from 'lucide-react';

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
  // State for form inputs
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  
  // State for UI status and results
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(-1);

  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  // Corrected handleSubmit function
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload a resume and paste a job description.');
      return;
    }

    setIsLoading(true);
    setError('');
    setAnalysisResult(null);

    // Create a FormData object to send the raw file and text
    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('job_description', jobDescription);

    try {
      // Make the API call to the intelligent backend.
      // Axios automatically sets the 'Content-Type' to 'multipart/form-data'
      // when you send a FormData object.
      const response = await axios.post('http://127.0.0.1:8000/gemini-analyze', formData);
      setAnalysisResult(response.data);

    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'An unexpected error occurred during analysis.';
      setError(`Analysis failed: ${errorMessage}`);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const copyToClipboard = (text, index) => {
    const tempTextArea = document.createElement('textarea');
    tempTextArea.value = text;
    document.body.appendChild(tempTextArea);
    tempTextArea.select();
    document.execCommand('copy');
    document.body.removeChild(tempTextArea);
    
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(-1), 2000); // Reset after 2 seconds
  };

  return (
    <div className="bg-slate-50 min-h-screen font-sans text-slate-800">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8">
        
        <header className="text-center mb-10">
          <div className="inline-flex items-center gap-3">
            <BrainCircuit className="w-10 h-10 text-indigo-600" />
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              Resume<span className="text-indigo-600">Enhancer</span>
            </h1>
          </div>
          <p className="mt-3 text-lg text-slate-600 max-w-2xl mx-auto">
            Get an intelligent, AI-powered analysis of your resume against any job.
          </p>
        </header>

        <main>
          {/* Form Section */}
          <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Resume Upload */}
                <div>
                  <label htmlFor="resume-upload" className="block text-lg font-semibold mb-2 flex items-center gap-2">
                    <Upload className="w-5 h-5" /> Upload Your Resume
                  </label>
                  <div className="relative border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors">
                    <input type="file" id="resume-upload" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={handleFileChange} accept=".pdf,.docx,.txt" />
                    <div className="flex flex-col items-center justify-center">
                      <FileText className="w-10 h-10 text-slate-400 mb-2" />
                      {resumeFile ? <p className="text-slate-700 font-medium">{resumeFile.name}</p> : <p className="text-slate-500">Click to upload</p>}
                      <p className="text-xs text-slate-400 mt-1">PDF, DOCX, or TXT</p>
                    </div>
                  </div>
                </div>
                {/* Job Description */}
                <div>
                  <label htmlFor="job-description" className="block text-lg font-semibold mb-2 flex items-center gap-2">
                    <FileText className="w-5 h-5" /> Job Description or Title
                  </label>
                  <textarea id="job-description" rows="8" className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition" placeholder="Paste the full job description or just a title like 'Senior Python Developer'..." value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} />
                </div>
              </div>
              <div className="mt-8 text-center">
                <button type="submit" className="bg-indigo-600 text-white font-bold text-lg py-3 px-8 rounded-lg hover:bg-indigo-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-all transform hover:scale-105 flex items-center justify-center gap-3 mx-auto" disabled={isLoading}>
                  {isLoading ? (<><Loader className="animate-spin w-6 h-6" /> Analyzing with AI...</>) : (<>Generate Analysis <ArrowRight className="w-6 h-6" /></>)}
                </button>
              </div>
            </form>
          </div>

          {/* Loading and Error States */}
          {isLoading && (
            <div className="text-center mt-8">
              <p className="text-lg text-slate-600">AI is analyzing... this may take up to 30 seconds.</p>
            </div>
          )}
          {error && <div className="max-w-4xl mx-auto mt-8 p-4 bg-red-100 text-red-800 border border-red-300 rounded-lg text-center">{error}</div>}

          {/* --- Intelligent Analysis Report --- */}
          {analysisResult && (
            <div className="max-w-4xl mx-auto mt-10 space-y-8 animate-fade-in">
              <h2 className="text-3xl font-bold text-center">Your AI-Powered Report</h2>
              
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
                        <ul className="list-disc list-inside mt-1">
                            {analysisResult.resume_feedback.strengths.map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-slate-700 flex items-center gap-2"><XCircle className="text-red-500"/> Areas for Improvement</h4>
                        <ul className="list-disc list-inside mt-1">
                            {analysisResult.resume_feedback.areas_for_improvement.map((item, i) => <li key={i}>{item}</li>)}
                        </ul>
                    </div>
                </div>
              </ReportSection>

              <ReportSection icon={<Sparkles className="w-7 h-7 text-fuchsia-500" />} title="Actionable Suggestions">
                <p>Copy these AI-generated bullet points and add them to your resume to address the gaps.</p>
                <div className="space-y-3 pt-2">
                  {analysisResult.actionable_suggestions.bullet_points.map((point, i) => (
                    <div key={i} className="bg-slate-100 p-3 rounded-lg flex items-start justify-between gap-4 border border-slate-200">
                      <p className="flex-grow">{point}</p>
                      <button onClick={() => copyToClipboard(point, i)} className="text-slate-500 hover:text-indigo-600 transition-colors p-1 rounded-md flex-shrink-0">
                        {copiedIndex === i ? <CheckCircle className="w-5 h-5 text-green-600" /> : <ClipboardCopy className="w-5 h-5" />}
                      </button>
                    </div>
                  ))}
                </div>
              </ReportSection>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
