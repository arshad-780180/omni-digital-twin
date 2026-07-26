import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { analyzeGitHub, getGitHubLatest } from '../services/github';
import {
  GitBranch,
  Loader2,
  Code2,
  FolderGit2,
  ChevronLeft,
  AlertCircle,
  Award,
  CheckCircle2,
  TrendingUp,
  BookOpen,
  ExternalLink,
  Star,
  GitFork,
  Sparkles,
  ShieldAlert,
  ArrowUpRight,
  UserCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function GitHubSync() {
  const { user } = useAuth();
  const [username, setUsername] = useState('');
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, error, success
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const fetchExisting = async () => {
      try {
        const data = await getGitHubLatest();
        if (data) {
          setReport(data);
          setStatus('success');
        }
      } catch (err) {
        if (err.response?.status !== 404) {
          console.error("Error fetching github report:", err);
        }
      }
    };
    fetchExisting();
  }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;

    setStatus('loading');
    setErrorMessage('');

    try {
      const data = await analyzeGitHub(username.trim());
      setReport(data);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze GitHub profile');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 65) return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="p-2 hover:bg-slate-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div className="text-xl font-bold flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-blue-400" />
            <span>AI GitHub Intelligence Engine</span>
          </div>
        </div>
        {status === 'success' && report && (
          <button
            onClick={() => {
              setUsername(report.username);
              setStatus('idle');
            }}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors border border-slate-700 flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-blue-400" />
            Analyze New Profile
          </button>
        )}
      </header>

      <main className="max-w-6xl mx-auto p-6 md:p-10">
        {status !== 'success' || !report ? (
          <div className="max-w-lg mx-auto mt-16 bg-slate-800/60 border border-slate-700 rounded-3xl p-8 backdrop-blur-md text-center shadow-2xl">
            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-blue-500/20">
              <GitBranch className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">AI GitHub Portfolio Audit</h2>
            <p className="text-slate-400 mb-8 text-sm leading-relaxed">
              Connect your GitHub profile to run a comprehensive engineering audit. Our AI engine evaluates repository architecture, code quality, developer maturity, and identifies missing skills relative to your resume.
            </p>

            {status === 'error' && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm flex items-center justify-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleAnalyze} className="space-y-4">
              <input
                type="text"
                placeholder="Enter GitHub Username (e.g. torvalds)"
                className="w-full bg-slate-900/70 border border-slate-700 text-slate-100 rounded-xl px-4 py-3.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-center placeholder:text-slate-500"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-700 text-white font-semibold py-3.5 rounded-xl flex justify-center items-center gap-2 transition-all shadow-lg shadow-blue-600/20"
              >
                {status === 'loading' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing Portfolio with AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Analyze Portfolio
                  </>
                )}
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Top Overview Banner */}
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-xl">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="flex items-center gap-5">
                  {report.profile?.avatar_url ? (
                    <img
                      src={report.profile.avatar_url}
                      alt={report.username}
                      className="w-20 h-20 rounded-2xl border-2 border-slate-700 shadow-md"
                    />
                  ) : (
                    <div className="w-20 h-20 rounded-2xl bg-blue-600/20 border-2 border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-2xl">
                      {report.username.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-3">
                      <h1 className="text-2xl md:text-3xl font-bold">{report.profile?.name || report.username}</h1>
                      <a
                        href={report.profile?.html_url || `https://github.com/${report.username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-slate-400 hover:text-blue-400 transition-colors"
                      >
                        <ExternalLink className="w-5 h-5" />
                      </a>
                    </div>
                    <p className="text-slate-400 text-sm mt-1 max-w-lg">
                      {report.profile?.bio || 'Software Developer & Open Source Contributor'}
                    </p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <FolderGit2 className="w-4 h-4 text-blue-400" />
                        <strong>{report.profile?.public_repos || report.repositories?.length || 0}</strong> Public Repos
                      </span>
                      <span className="flex items-center gap-1">
                        <UserCheck className="w-4 h-4 text-emerald-400" />
                        <strong>{report.profile?.followers || 0}</strong> Followers
                      </span>
                    </div>
                  </div>
                </div>

                {/* Score and Developer Level Badge */}
                <div className="flex items-center gap-4 w-full md:w-auto justify-end border-t md:border-t-0 pt-4 md:pt-0 border-slate-700">
                  <div className="text-right">
                    <p className="text-xs text-slate-400 uppercase font-semibold tracking-wider">Developer Level</p>
                    <span className="inline-block mt-1 px-3 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-300 font-semibold rounded-lg text-sm">
                      {report.analysis?.developer_level || 'Mid-Level'}
                    </span>
                  </div>
                  <div className={`flex flex-col items-center justify-center w-24 h-24 rounded-2xl border-2 ${getScoreColor(report.analysis?.github_score || 75)}`}>
                    <span className="text-3xl font-extrabold">{report.analysis?.github_score || 75}</span>
                    <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">GitHub Score</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Portfolio Executive Review */}
            <div className="bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 border border-blue-500/20 rounded-3xl p-6 md:p-8 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/20 rounded-xl text-blue-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold">Executive Portfolio Review</h3>
              </div>
              <p className="text-slate-200 leading-relaxed text-sm md:text-base">
                {report.analysis?.portfolio_review || 'No executive summary available.'}
              </p>
            </div>

            {/* Strengths & Weaknesses Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-3xl p-6 backdrop-blur-md">
                <div className="flex items-center gap-3 mb-4 text-emerald-400">
                  <CheckCircle2 className="w-6 h-6" />
                  <h3 className="text-lg font-bold text-slate-100">Key Engineering Strengths</h3>
                </div>
                <ul className="space-y-3">
                  {(report.analysis?.strengths || []).map((strength, idx) => (
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
                  <h3 className="text-lg font-bold text-slate-100">Areas for Growth</h3>
                </div>
                <ul className="space-y-3">
                  {(report.analysis?.weaknesses || []).map((weakness, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm text-slate-300">
                      <span className="w-2 h-2 rounded-full bg-amber-400 mt-2 shrink-0"></span>
                      <span>{weakness}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Missing Skills (Comparison with Resume) */}
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-500/20 rounded-xl text-purple-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">Missing Skills (GitHub vs. Resume Audit)</h3>
                  <p className="text-xs text-slate-400">Skills missing from your public GitHub footprint relative to your resume or senior industry benchmarks</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mt-4">
                {(report.analysis?.missing_skills || []).map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/30 text-purple-300 rounded-xl text-xs font-medium flex items-center gap-1.5"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Repository Analysis Grid */}
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/20 rounded-xl text-blue-400">
                  <Code2 className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold">Repository Architecture & Quality</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(report.analysis?.repository_analysis || []).map((repo, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-900/60 border border-slate-700/70 rounded-2xl p-5 hover:border-blue-500/40 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-bold text-slate-200 text-base flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-blue-400" />
                        {repo.name}
                      </h4>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded text-xs">
                          Quality: {repo.quality_score}%
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mb-3 line-clamp-2">{repo.summary}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {(repo.technologies || []).map((tech, i) => (
                        <span key={i} className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-[11px]">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Personalized Learning Roadmap */}
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-emerald-500/20 rounded-xl text-emerald-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold">Personalized Learning Roadmap</h3>
              </div>

              <div className="space-y-6">
                {(report.analysis?.personalized_roadmap || []).map((step, idx) => (
                  <div key={idx} className="flex gap-4 items-start">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0 mt-1">
                      {step.step_number || idx + 1}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-100">{step.title}</h4>
                      <p className="text-sm text-slate-300 mt-1">{step.description}</p>
                      {step.recommended_resources?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {step.recommended_resources.map((res, i) => (
                            <span
                              key={i}
                              className="px-2.5 py-1 bg-slate-900/80 border border-slate-700 text-slate-400 rounded-lg text-xs"
                            >
                              📚 {res}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
