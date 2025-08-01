import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, BrainCircuit, CheckCircle, XCircle, Loader, ArrowRight } from 'lucide-react';

// Main App Component
const App = () => {
  // State variables to manage form data, results, and UI status
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Handler for file input changes
  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  // Handler for form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission behavior
    
    // Basic validation
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload a resume and paste a job description.');
      return;
    }

    // Reset UI state for a new analysis
    setIsLoading(true);
    setError('');
    setAnalysisResult(null);

    // Create a FormData object to send file and text data
    const formData = new FormData();
    formData.append('resume', resumeFile);
    formData.append('job_description', jobDescription);

    try {
      // Make the API call to the backend
      const response = await axios.post('http://127.0.0.1:8000/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // Store the successful response
      setAnalysisResult(response.data);
    } catch (err) {
      // Handle errors from the API call
      const errorMessage = err.response?.data?.detail || 'An unexpected error occurred.';
      setError(`Analysis failed: ${errorMessage}`);
      console.error(err);
    } finally {
      // Ensure loading is turned off after the request completes
      setIsLoading(false);
    }
  };

  // --- JSX for Rendering the UI ---
  return (
    <div className="bg-slate-50 min-h-screen font-sans text-slate-800">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8">
        
        {/* Header Section */}
        <header className="text-center mb-10">
          <div className="inline-flex items-center gap-3">
            <BrainCircuit className="w-10 h-10 text-indigo-600" />
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
              Resume<span className="text-indigo-600">Enhancer</span>
            </h1>
          </div>
          <p className="mt-3 text-lg text-slate-600 max-w-2xl mx-auto">
            Analyze your resume against a job description to get a match score and keyword insights.
          </p>
        </header>

        <main>
          {/* Form Section */}
          <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Resume Upload Area */}
                <div>
                  <label htmlFor="resume-upload" className="block text-lg font-semibold mb-2 flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    Upload Your Resume
                  </label>
                  <div className="relative border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors">
                    <input
                      type="file"
                      id="resume-upload"
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      onChange={handleFileChange}
                      accept=".pdf,.docx"
                    />
                    <div className="flex flex-col items-center justify-center">
                      <FileText className="w-10 h-10 text-slate-400 mb-2" />
                      {resumeFile ? (
                        <p className="text-slate-700 font-medium">{resumeFile.name}</p>
                      ) : (
                        <p className="text-slate-500">Click to upload or drag & drop</p>
                      )}
                      <p className="text-xs text-slate-400 mt-1">PDF or DOCX</p>
                    </div>
                  </div>
                </div>

                {/* Job Description Text Area */}
                <div>
                  <label htmlFor="job-description" className="block text-lg font-semibold mb-2 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Paste Job Description
                  </label>
                  <textarea
                    id="job-description"
                    rows="8"
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                    placeholder="Paste the full job description here..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="mt-8 text-center">
                <button
                  type="submit"
                  className="bg-indigo-600 text-white font-bold text-lg py-3 px-8 rounded-lg hover:bg-indigo-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-all transform hover:scale-105 flex items-center justify-center gap-3 mx-auto"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader className="animate-spin w-6 h-6" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      Analyze Now
                      <ArrowRight className="w-6 h-6" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Results Section */}
          {error && (
            <div className="max-w-4xl mx-auto mt-8 p-4 bg-red-100 text-red-800 border border-red-300 rounded-lg text-center">
              {error}
            </div>
          )}

          {analysisResult && (
            <div className="max-w-4xl mx-auto mt-10 bg-white p-8 rounded-2xl shadow-lg border border-slate-200 animate-fade-in">
              <h2 className="text-3xl font-bold text-center mb-8">Analysis Results</h2>
              
              {/* Score Gauge */}
              <div className="flex justify-center items-center mb-8">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full" viewBox="0 0 36 36">
                    <path
                      className="text-slate-200"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                    />
                    <path
                      className="text-indigo-600"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeDasharray={`${analysisResult.match_score}, 100`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-4xl font-bold text-indigo-600">{analysisResult.match_score}%</span>
                    <span className="text-lg text-slate-600">Match Score</span>
                  </div>
                </div>
              </div>

              {/* Keyword Analysis */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Matched Keywords */}
                <div className="bg-green-50 p-6 rounded-lg border border-green-200">
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-green-800">
                    <CheckCircle />
                    Matched Keywords ({analysisResult.matched_keywords.length})
                  </h3>
                  <ul className="space-y-2 max-h-48 overflow-y-auto">
                    {analysisResult.matched_keywords.map((keyword, index) => (
                      <li key={index} className="bg-green-100 text-green-900 px-3 py-1 rounded-full text-sm inline-block mr-2 mb-2">
                        {keyword}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Missing Keywords */}
                <div className="bg-amber-50 p-6 rounded-lg border border-amber-200">
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-amber-800">
                    <XCircle />
                    Missing Keywords ({analysisResult.missing_keywords.length})
                  </h3>
                  <ul className="space-y-2 max-h-48 overflow-y-auto">
                    {analysisResult.missing_keywords.map((keyword, index) => (
                      <li key={index} className="bg-amber-100 text-amber-900 px-3 py-1 rounded-full text-sm inline-block mr-2 mb-2">
                        {keyword}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
