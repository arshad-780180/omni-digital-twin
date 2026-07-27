import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  analyzeATS,
  getATSLatest,
  getATSHistory,
  deleteATSAnalysis
} from '../services/ats';
import {
  FileCheck2,
  Loader2,
  ChevronLeft,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Trash2,
  History,
  TrendingUp,
  Award,
  FileText,
  RefreshCw,
  Briefcase,
  Layers,
  Copy,
  Check
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ATSOptimizer() {
  const { user } = useAuth();
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, loading, error, success
  const [errorMessage, setErrorMessage] = useState('');
  const [copiedSection, setCopiedSection] = useState('');

  // Form State
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [jobDescription, setJobDescription] = useState('');

  useEffect(() => {
    fetchLatestAndHistory();
  }, []);

  const fetchLatestAndHistory = async () => {
    try {
      const [latestData, historyData] = await Promise.all([
        getATSLatest().catch(() => null),
        getATSHistory().catch(() => [])
      ]);
      if (latestData) {
        setReport(latestData);
      }
      setHistory(historyData);
    } catch (err) {
      console.error("Error loading ATS history:", err);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!jobTitle.trim() || !jobDescription.trim()) return;
    setStatus('loading');
    setErrorMessage('');
    try {
      const data = await analyzeATS(jobTitle.trim(), company.trim(), jobDescription.trim());
      setReport(data);
      setStatus('success');
      fetchLatestAndHistory();
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze resume against job description.');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteATSAnalysis(id);
      if (report && report.id === id) {
        setReport(null);
      }
      fetchLatestAndHistory();
    } catch (err) {
      console.error("Failed to delete ATS report:", err);
    }
  };

  const handleCopyText = (text, label) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(label);
    setTimeout(() => setCopiedSection(''), 2000);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10 stroke-emerald-400';
    if (score >= 65) return 'text-blue-400 border-blue-500/30 bg-blue-500/10 stroke-blue-400';
    return 'text-amber-400 border-amber-500/30 bg-amber-500/10 stroke-amber-400';
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-20">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="p-2 hover:bg-slate-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div className="text-xl font-bold flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-emerald-400" />
            <span>AI ATS Resume Optimizer</span>
          </div>
        </div>

        <button
          onClick={() => {
            setJobTitle('');
            setCompany('');
            setJobDescription('');
            setStatus('idle');
          }}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          New Target Job
        </button>
      </header>

      <main className="max-w-7xl mx-auto p-6 md:p-10 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Target Job Form */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400">
                <Briefcase className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold">Target Job Description</h2>
                <p className="text-xs text-slate-400">We automatically compare against your latest resume</p>
              </div>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Job Title *
                </label>
                <input
                  type="text"
                  required
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g. Senior Python Backend Engineer"
                  className="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Company (Optional)
                </label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Google / Microsoft / Stripe"
                  className="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Paste Job Description *
                </label>
                <textarea
                  required
                  rows="8"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the full job responsibilities and technical requirements..."
                  className="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 transition-colors resize-none leading-relaxed"
                />
              </div>

              {status === 'error' && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:from-slate-700 disabled:to-slate-700 text-white font-semibold py-3.5 rounded-xl flex justify-center items-center gap-2 transition-all shadow-lg shadow-emerald-600/20 text-sm"
              >
                {status === 'loading' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Optimizing Resume with AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Optimize Resume Against Job
                  </>
                )}
              </button>
            </form>
          </div>

          {/* History Table Card */}
          {history.length > 0 && (
            <div className="bg-slate-800/40 border border-slate-700/70 rounded-3xl p-6 backdrop-blur-md">
              <div className="flex items-center gap-2 mb-4 text-slate-300">
                <History className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold">Past ATS Analyses</h3>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 bg-slate-900/50 rounded-xl border border-slate-800 hover:border-slate-700 transition-all text-xs"
                  >
                    <div
                      onClick={() => setReport(item)}
                      className="cursor-pointer flex-grow pr-3"
                    >
                      <p className="font-bold text-slate-200 truncate">{item.job_title}</p>
                      <p className="text-slate-400 mt-0.5">
                        {item.company || 'Company N/A'} • Score: <strong className="text-emerald-400">{item.ats_score}%</strong>
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg transition-colors"
                      title="Delete analysis"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: ATS Analysis & Suggestions */}
        <div className="lg:col-span-7 space-y-6">
          {report ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Hero ATS Score Card */}
              <div className="bg-gradient-to-br from-slate-800/80 via-slate-800/50 to-slate-900 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold uppercase tracking-wider">
                    ATS Keyword & Role Fit
                  </span>
                  <h1 className="text-2xl md:text-3xl font-extrabold mt-3 text-slate-100">
                    {report.job_title}
                  </h1>
                  <p className="text-slate-400 text-xs mt-1">
                    {report.company ? `Target Company: ${report.company}` : 'General Role Analysis'}
                  </p>
                </div>

                <div className="flex items-center gap-6">
                  <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="42" fill="transparent" strokeWidth="8" className="stroke-slate-800" />
                      <circle
                        cx="50" cy="50" r="42" fill="transparent" strokeWidth="8"
                        strokeDasharray="264"
                        strokeDashoffset={264 - (264 * report.ats_score) / 100}
                        strokeLinecap="round"
                        className={`transition-all duration-1000 ease-out ${getScoreColor(report.ats_score).split(' ')[3]}`}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-extrabold">
                        {report.ats_score}
                      </span>
                      <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">/ 100</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Keyword Match & Gap Audit */}
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
                <h3 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-emerald-400" />
                  Keyword Match Audit
                </h3>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Matched Keywords ({report.matched_keywords?.length || 0})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {report.matched_keywords?.map((kw, idx) => (
                        <span key={idx} className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-xl text-xs font-medium">
                          ✓ {kw}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Missing Keywords ({report.missing_keywords?.length || 0})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {report.missing_keywords?.map((kw, idx) => (
                        <span key={idx} className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-300 rounded-xl text-xs font-medium">
                          ! {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Resume Improvement Suggestions Card */}
              {report.ai_suggestions && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-emerald-400" />
                      AI Resume Improvement Suggestions
                    </h3>
                  </div>

                  {/* Improved Professional Summary */}
                  {report.ai_suggestions.improved_summary && (
                    <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                          Optimized Professional Summary
                        </h4>
                        <button
                          onClick={() => handleCopyText(report.ai_suggestions.improved_summary, 'summary')}
                          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          {copiedSection === 'summary' ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                      <p className="text-sm text-slate-200 leading-relaxed">
                        {report.ai_suggestions.improved_summary}
                      </p>
                    </div>
                  )}

                  {/* Improved Project Descriptions */}
                  {report.ai_suggestions.improved_projects?.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                        Improved Project Bullet Points (Quantified & Action-Driven)
                      </h4>
                      <div className="space-y-2">
                        {report.ai_suggestions.improved_projects.map((proj, idx) => (
                          <div key={idx} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-xs text-slate-300 leading-relaxed flex items-start justify-between gap-3">
                            <span>• {proj}</span>
                            <button
                              onClick={() => handleCopyText(proj, `proj-${idx}`)}
                              className="text-slate-500 hover:text-slate-300 shrink-0"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Keyword Injection Advice */}
                  {report.ai_suggestions.keyword_injection?.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400 mb-2">
                        Keyword Injection Strategies
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-300">
                        {report.ai_suggestions.keyword_injection.map((inj, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-purple-400 font-bold">→</span>
                            <span>{inj}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Resume Feedback Card */}
              {report.resume_feedback && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Resume Strengths
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {report.resume_feedback.strengths?.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-amber-400 mb-3 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Actionable Recommendations
                    </h4>
                    <ul className="space-y-2 text-xs text-slate-300">
                      {report.resume_feedback.recommendations?.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0"></span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[480px] bg-slate-800/30 border-2 border-dashed border-slate-700/80 rounded-3xl flex flex-col items-center justify-center p-8 text-center">
              <div className="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-4 border border-emerald-500/20">
                <FileCheck2 className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-200">Ready for ATS Optimization</h3>
              <p className="text-slate-400 text-xs max-w-sm mt-1 leading-relaxed">
                Enter your target Job Title and paste the Job Description on the left. We will evaluate keyword overlap, calculate your ATS score, and generate tailored AI resume improvements.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
