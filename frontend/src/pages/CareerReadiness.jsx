import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  analyzeCareerReadiness,
  getCareerLatest,
  getCareerHistory,
  analyzeJob
} from '../services/career';
import {
  Target,
  Loader2,
  ChevronLeft,
  Award,
  Briefcase,
  Code2,
  FileText,
  GitBranch,
  FolderGit2,
  MessageSquare,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ShieldAlert,
  RefreshCw,
  Layers
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CareerReadiness() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('audit'); // 'audit' | 'legacy_ats'
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, loading, error, success
  const [errorMessage, setErrorMessage] = useState('');

  // Legacy ATS state
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [atsReport, setAtsReport] = useState(null);

  useEffect(() => {
    fetchLatestAndHistory();
  }, []);

  const fetchLatestAndHistory = async () => {
    try {
      const [latestData, historyData] = await Promise.all([
        getCareerLatest().catch(() => null),
        getCareerHistory().catch(() => [])
      ]);
      if (latestData) {
        setReport(latestData);
        setStatus('success');
      }
      setHistory(historyData);
    } catch (err) {
      console.error("Error fetching career readiness:", err);
    }
  };

  const handleRunAudit = async () => {
    setStatus('loading');
    setErrorMessage('');
    try {
      const data = await analyzeCareerReadiness();
      setReport(data);
      setStatus('success');
      fetchLatestAndHistory();
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to generate AI career audit.');
    }
  };

  const handleLegacyAtsMatch = async (e) => {
    e.preventDefault();
    if (!jobTitle.trim() || !jobDescription.trim()) return;
    setStatus('loading');
    setErrorMessage('');
    try {
      const res = await analyzeJob(jobTitle.trim(), jobDescription.trim());
      setAtsReport(res);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze ATS job match.');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10 stroke-emerald-400';
    if (score >= 65) return 'text-blue-400 border-blue-500/30 bg-blue-500/10 stroke-blue-400';
    return 'text-amber-400 border-amber-500/30 bg-amber-500/10 stroke-amber-400';
  };

  const getLevelBadgeColor = (level) => {
    switch (level) {
      case 'Advanced':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'Placement Ready':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'Intermediate':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40';
    }
  };

  const scoreCards = report ? [
    {
      title: 'Technical Mastery',
      score: report.technical_score || report.breakdown?.technical_score || 80,
      icon: Code2,
      color: 'from-blue-500/20 to-indigo-500/20',
      description: 'Languages, backend & frontend architecture'
    },
    {
      title: 'Resume Quality',
      score: report.resume_score || report.breakdown?.resume_score || 80,
      icon: FileText,
      color: 'from-emerald-500/20 to-teal-500/20',
      description: 'ATS formatting, experience & clarity'
    },
    {
      title: 'GitHub Footprint',
      score: report.github_score || report.breakdown?.github_score || 80,
      icon: GitBranch,
      color: 'from-purple-500/20 to-pink-500/20',
      description: 'Public commits, stars, & open-source activity'
    },
    {
      title: 'Project Complexity',
      score: report.project_score || report.breakdown?.project_score || 80,
      icon: FolderGit2,
      color: 'from-amber-500/20 to-orange-500/20',
      description: 'System design, testing & deployment maturity'
    },
    {
      title: 'Communication',
      score: report.communication_score || report.breakdown?.communication_score || 80,
      icon: MessageSquare,
      color: 'from-cyan-500/20 to-blue-500/20',
      description: 'README clarity, documentation & teamwork'
    }
  ] : [];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-16">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="p-2 hover:bg-slate-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div className="text-xl font-bold flex items-center gap-2">
            <Target className="w-6 h-6 text-blue-400" />
            <span>AI Career Readiness Engine</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-800/80 p-1 rounded-xl border border-slate-700 flex">
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'audit'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Core AI Audit
            </button>
            <button
              onClick={() => setActiveTab('legacy_ats')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'legacy_ats'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Legacy ATS Match
            </button>
          </div>

          {activeTab === 'audit' && (
            <button
              onClick={handleRunAudit}
              disabled={status === 'loading'}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-lg shadow-blue-600/20"
            >
              {status === 'loading' ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Refresh Audit
                </>
              )}
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 md:p-10">
        {status === 'error' && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm flex items-center justify-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {activeTab === 'audit' ? (
          !report ? (
            <div className="max-w-lg mx-auto mt-16 bg-slate-800/60 border border-slate-700 rounded-3xl p-8 backdrop-blur-md text-center shadow-2xl">
              <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-blue-500/20">
                <Target className="w-8 h-8 text-blue-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Omni Core Intelligence Audit</h2>
              <p className="text-slate-400 mb-8 text-sm leading-relaxed">
                Generate a unified AI career readiness report by synthesizing your parsed Resume (Phase 1), GitHub engineering footprint (Phase 2), and user profile skills.
              </p>
              <button
                onClick={handleRunAudit}
                disabled={status === 'loading'}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-700 text-white font-semibold py-3.5 rounded-xl flex justify-center items-center gap-2 transition-all shadow-lg shadow-blue-600/20"
              >
                {status === 'loading' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Synthesizing Core Intelligence...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate AI Career Audit
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Hero Card */}
              <div className="bg-gradient-to-br from-slate-800/80 via-slate-800/50 to-slate-900 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl">
                <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                  <div className="flex flex-col items-start space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs font-semibold uppercase tracking-wider">
                        OMNI Core Intelligence
                      </span>
                      <span className={`px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-wider ${getLevelBadgeColor(report.career_level)}`}>
                        ★ {report.career_level}
                      </span>
                    </div>
                    <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">
                      AI Career Readiness Audit
                    </h1>
                    <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
                      Synthesized from your parsed resume, live GitHub repositories, and user profile data. Your digital twin is currently evaluated as <strong>{report.career_level}</strong> for engineering roles.
                    </p>
                  </div>

                  {/* Hero Large Circular Score */}
                  <div className="flex items-center gap-6">
                    <div className="relative w-36 h-36 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="42" fill="transparent" strokeWidth="8" className="stroke-slate-800" />
                        <circle
                          cx="50" cy="50" r="42" fill="transparent" strokeWidth="8"
                          strokeDasharray="264"
                          strokeDashoffset={264 - (264 * (report.career_score || report.overall_score || 80)) / 100}
                          strokeLinecap="round"
                          className={`transition-all duration-1000 ease-out ${getScoreColor(report.career_score || report.overall_score || 80).split(' ')[3]}`}
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-4xl font-extrabold">
                          {report.career_score || report.overall_score || 80}
                        </span>
                        <span className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">/ 100</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Score Breakdown Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {scoreCards.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={idx}
                      className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-sm hover:border-slate-600 transition-colors flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <div className={`p-2 rounded-xl bg-gradient-to-br ${card.color} text-blue-400`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <span className="text-xl font-bold text-slate-100">{card.score}%</span>
                        </div>
                        <h3 className="font-bold text-sm text-slate-200 mb-1">{card.title}</h3>
                        <p className="text-xs text-slate-400 line-clamp-2">{card.description}</p>
                      </div>
                      <div className="w-full bg-slate-700/60 h-1.5 rounded-full mt-4 overflow-hidden">
                        <div
                          className="bg-blue-500 h-full rounded-full transition-all duration-700"
                          style={{ width: `${card.score}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Career Executive Summary */}
              <div className="bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 border border-blue-500/20 rounded-3xl p-6 md:p-8 backdrop-blur-md">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-blue-500/20 rounded-xl text-blue-400">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold">AI Executive Career Summary</h3>
                </div>
                <p className="text-slate-200 leading-relaxed text-sm md:text-base">
                  {report.summary || 'No summary generated yet.'}
                </p>
              </div>

              {/* Strengths & Growth Areas Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 backdrop-blur-md">
                  <div className="flex items-center gap-3 mb-4 text-emerald-400">
                    <CheckCircle2 className="w-6 h-6" />
                    <h3 className="text-lg font-bold text-slate-100">Core Engineering Strengths</h3>
                  </div>
                  <ul className="space-y-3">
                    {(report.strengths || []).map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm text-slate-300">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 mt-2 shrink-0"></span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 backdrop-blur-md">
                  <div className="flex items-center gap-3 mb-4 text-amber-400">
                    <TrendingUp className="w-6 h-6" />
                    <h3 className="text-lg font-bold text-slate-100">Areas for Growth & Weaknesses</h3>
                  </div>
                  <ul className="space-y-3">
                    {(report.weaknesses || []).map((weakness, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm text-slate-300">
                        <span className="w-2 h-2 rounded-full bg-amber-400 mt-2 shrink-0"></span>
                        <span>{weakness}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Missing Skills Chips */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-purple-500/20 rounded-xl text-purple-400">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Missing Skills Audit</h3>
                    <p className="text-xs text-slate-400">Core technologies missing from your digital twin relative to target engineering benchmarks</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  {(report.missing_skills || []).map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3.5 py-2 bg-purple-500/10 border border-purple-500/30 text-purple-300 rounded-xl text-xs font-semibold flex items-center gap-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Recommended Roles Cards Grid */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-blue-500/20 rounded-xl text-blue-400">
                    <Briefcase className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Recommended Engineering Roles</h3>
                    <p className="text-xs text-slate-400">Roles best matching your current technical skillset and GitHub profile</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                  {(report.recommended_roles || []).map((role, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5 hover:border-blue-500/40 transition-all flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <Award className="w-5 h-5 text-blue-400" />
                        <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          Top Match
                        </span>
                      </div>
                      <h4 className="font-bold text-slate-100 text-base">{role}</h4>
                      <p className="text-xs text-slate-400 mt-1">High synergy with your Python & backend stack</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        ) : (
          /* Legacy ATS Job Match Tab */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-blue-400" />
                  Legacy ATS Job Match
                </h2>

                <form onSubmit={handleLegacyAtsMatch} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1">Job Title</label>
                    <input
                      type="text"
                      className="w-full bg-slate-900/50 border border-slate-700 text-slate-100 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="e.g. Senior Backend Developer"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1">Job Description</label>
                    <textarea
                      className="w-full h-44 bg-slate-900/50 border border-slate-700 text-slate-100 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 resize-none"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste job description here..."
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-semibold py-3 rounded-xl flex justify-center items-center gap-2 transition-all"
                  >
                    {status === 'loading' ? 'Matching ATS...' : 'Generate ATS Match'}
                  </button>
                </form>
              </div>
            </div>

            <div className="lg:col-span-7">
              {atsReport ? (
                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur-sm">
                  <h2 className="text-2xl font-bold">{atsReport.job_title}</h2>
                  <p className="text-slate-400 mt-1">ATS Match Score: {atsReport.match_score}%</p>
                  <div className="mt-6 space-y-4">
                    <div>
                      <h4 className="text-emerald-400 font-bold mb-2">Matched Skills</h4>
                      <div className="flex flex-wrap gap-2">
                        {atsReport.matched_skills?.map((sk, i) => (
                          <span key={i} className="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-sm">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-red-400 font-bold mb-2">Missing Skills</h4>
                      <div className="flex flex-wrap gap-2">
                        {atsReport.missing_skills?.map((sk, i) => (
                          <span key={i} className="px-3 py-1 bg-red-500/20 text-red-300 rounded-full text-sm">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-700 rounded-2xl">
                  <p className="text-lg font-medium">Ready for ATS Analysis</p>
                  <p className="text-sm max-w-xs text-center mt-2">
                    Paste a job description on the left to see your ATS keyword match score.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
