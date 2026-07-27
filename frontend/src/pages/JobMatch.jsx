import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  analyzeJobMatch,
  getJobMatchLatest,
  getJobMatchHistory,
  deleteJobMatch,
} from '../services/jobs';
import {
  Briefcase,
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
  Layers,
  DollarSign,
  BookOpen,
  Compass,
  Check,
  XCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function JobMatch() {
  const { user } = useAuth();
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [employmentType, setEmploymentType] = useState('Full-time');
  const [jobDescription, setJobDescription] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeAdviceTab, setActiveAdviceTab] = useState('summary');

  useEffect(() => {
    fetchLatestAnalysis();
    fetchHistory();
  }, []);

  const fetchLatestAnalysis = async () => {
    try {
      const data = await getJobMatchLatest();
      if (data && data.overall_job_match_score !== undefined) {
        setAnalysis(data);
      }
    } catch (err) {
      // No existing analysis found
    }
  };

  const fetchHistory = async () => {
    try {
      const list = await getJobMatchHistory();
      if (Array.isArray(list)) {
        setHistory(list);
      }
    } catch (err) {
      console.error('Failed to fetch job match history:', err);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!jobTitle.trim() || !jobDescription.trim()) {
      setError('Please provide both a Job Title and a Job Description.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await analyzeJobMatch({
        job_title: jobTitle,
        company: company,
        location: location,
        employment_type: employmentType,
        job_description: jobDescription,
      });
      setAnalysis(result);
      fetchHistory();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to analyze job match. Please check your network or try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (matchId) => {
    try {
      await deleteJobMatch(matchId);
      if (analysis && analysis.id === matchId) {
        setAnalysis(null);
      }
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete job match report:', err);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/50 bg-emerald-500/10';
    if (score >= 65) return 'text-blue-400 border-blue-500/50 bg-blue-500/10';
    if (score >= 50) return 'text-amber-400 border-amber-500/50 bg-amber-500/10';
    return 'text-red-400 border-red-500/50 bg-red-500/10';
  };

  const getRecommendationBadge = (rec) => {
    switch (rec) {
      case 'Strong Hire':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50';
      case 'Hire':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/50';
      case 'Consider':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/50';
      default:
        return 'bg-red-500/20 text-red-300 border-red-500/50';
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex justify-between items-center backdrop-blur-sm sticky top-0 z-10 bg-slate-900/80">
        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-emerald-400" />
            AI Job Matching Engine
          </h1>
        </div>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium border border-slate-700 transition-colors"
        >
          <History className="w-4 h-4 text-blue-400" />
          History ({history.length})
        </button>
      </header>

      <main className="flex-grow p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Job Description Input Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
            <h2 className="text-lg font-bold flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              Target Job Description
            </h2>

            {error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-sm text-red-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Job Title *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Senior Backend Engineer"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 text-slate-100"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Company
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Google"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Employment Type
                  </label>
                  <select
                    value={employmentType}
                    onChange={(e) => setEmploymentType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 text-slate-100"
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Internship">Internship</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Location
                </label>
                <input
                  type="text"
                  placeholder="e.g. Remote / San Francisco, CA"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Job Description *
                </label>
                <textarea
                  rows={8}
                  placeholder="Paste the full job description here..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 text-slate-100 font-mono"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-emerald-500 to-blue-600 hover:from-emerald-600 hover:to-blue-700 rounded-lg font-semibold text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Evaluating Match...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Analyze Job Match
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Analysis Dashboard & Results */}
        <div className="lg:col-span-2 space-y-6">
          {analysis ? (
            <>
              {/* Header Card with Circular Overall Score */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div
                    className={`w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center font-extrabold ${getScoreColor(
                      analysis.overall_job_match_score
                    )} shadow-xl`}
                  >
                    <span className="text-3xl">{analysis.overall_job_match_score}%</span>
                    <span className="text-[10px] uppercase tracking-wider opacity-75">
                      Match
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h2 className="text-2xl font-bold text-slate-100">
                        {analysis.job_title}
                      </h2>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold border ${getRecommendationBadge(
                          analysis.hiring_recommendation
                        )}`}
                      >
                        {analysis.hiring_recommendation}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400">
                      {analysis.company ? `${analysis.company} • ` : ''}
                      {analysis.location || 'Remote'} ({analysis.employment_type || 'Full-time'})
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      Readiness Level:{' '}
                      <span className="font-semibold text-slate-300">
                        {analysis.career_readiness}
                      </span>{' '}
                      • Method:{' '}
                      <span className="font-semibold text-slate-300 uppercase">
                        {analysis.analysis_method}
                      </span>
                    </p>
                  </div>
                </div>
              </div>

              {/* Multi-Dimensional Technical Breakdown */}
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
                <h3 className="text-md font-bold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Multi-Dimensional Match Breakdown
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Technical Skill Match</span>
                      <span className="font-bold text-slate-200">
                        {analysis.technical_match_score}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${analysis.technical_match_score}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Experience Alignment</span>
                      <span className="font-bold text-slate-200">
                        {analysis.experience_match_score}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${analysis.experience_match_score}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Education Requirement</span>
                      <span className="font-bold text-slate-200">
                        {analysis.education_match_score}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500 rounded-full"
                        style={{ width: `${analysis.education_match_score}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Project Relevance</span>
                      <span className="font-bold text-slate-200">
                        {analysis.project_relevance_score}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full"
                        style={{ width: `${analysis.project_relevance_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Matched vs Missing Skills Badges */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-5 backdrop-blur-sm">
                  <h4 className="text-sm font-bold text-emerald-400 flex items-center gap-2 mb-3">
                    <CheckCircle2 className="w-4 h-4" />
                    Matched Skills & Strengths
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {(analysis.matched_skills || []).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-md text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                    {(!analysis.matched_skills || analysis.matched_skills.length === 0) && (
                      <span className="text-xs text-slate-500 italic">No direct matches identified.</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-5 backdrop-blur-sm">
                  <h4 className="text-sm font-bold text-red-400 flex items-center gap-2 mb-3">
                    <XCircle className="w-4 h-4" />
                    Missing Technologies
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {(analysis.missing_skills || []).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 bg-red-500/10 border border-red-500/30 text-red-300 rounded-md text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                    {(!analysis.missing_skills || analysis.missing_skills.length === 0) && (
                      <span className="text-xs text-emerald-400 italic">
                        All target skills covered!
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Salary Insights Card with Explicit Market Disclaimer */}
              {analysis.salary_estimate && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-md font-bold flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-emerald-400" />
                      Salary Insights
                    </h3>
                    <span className="text-xs px-2.5 py-1 bg-blue-500/20 text-blue-300 border border-blue-500/40 rounded-full font-medium">
                      Confidence: {analysis.salary_estimate.confidence_level}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Junior Range</span>
                      <span className="text-lg font-bold text-slate-200">
                        {analysis.salary_estimate.junior_range}
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-4 rounded-lg border border-emerald-500/40">
                      <span className="text-xs text-emerald-400 block mb-1">Mid-Level Range (Target)</span>
                      <span className="text-lg font-bold text-emerald-300">
                        {analysis.salary_estimate.mid_level_range}
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block mb-1">Senior Range</span>
                      <span className="text-lg font-bold text-slate-200">
                        {analysis.salary_estimate.senior_range}
                      </span>
                    </div>
                  </div>

                  {/* Required Explicit Disclaimer */}
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-200 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-400" />
                    <span>{analysis.salary_estimate.disclaimer}</span>
                  </div>
                </div>
              )}

              {/* Role Recommendations */}
              {analysis.recommended_roles && analysis.recommended_roles.length > 0 && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
                  <h3 className="text-md font-bold mb-4 flex items-center gap-2">
                    <Compass className="w-5 h-5 text-blue-400" />
                    Role Recommendations & Alternatives
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysis.recommended_roles.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm text-slate-200">
                              {item.role_name}
                            </span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded font-bold ${
                                item.category === 'best_matching'
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : item.category === 'alternative'
                                  ? 'bg-blue-500/20 text-blue-300'
                                  : item.category === 'stretch'
                                  ? 'bg-purple-500/20 text-purple-300'
                                  : 'bg-red-500/20 text-red-300'
                              }`}
                            >
                              {item.match_percentage}% Match
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            {item.explanation}
                          </p>
                        </div>
                        <span className="text-[10px] uppercase tracking-wider text-slate-500 mt-3 font-semibold">
                          Category: {item.category.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Personalized Learning Gap Roadmap */}
              {analysis.learning_plan && analysis.learning_plan.length > 0 && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
                  <h3 className="text-md font-bold mb-4 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-purple-400" />
                    Learning Gap Analysis & Roadmap
                  </h3>
                  <div className="space-y-3">
                    {analysis.learning_plan.map((gap, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-900/60 border border-slate-800 p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4"
                      >
                        <div className="flex items-start gap-3">
                          <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                            #{gap.priority_order}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-slate-200">
                                {gap.skill}
                              </span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                                {gap.estimated_difficulty}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">{gap.reasoning}</p>
                          </div>
                        </div>
                        <div className="text-xs text-purple-300 font-semibold bg-purple-900/30 border border-purple-500/30 px-3 py-1.5 rounded-full flex-shrink-0 self-start md:self-center">
                          Timeline: {gap.learning_timeline}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Career Advice Accordion / Tabs */}
              {analysis.career_advice && (
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 backdrop-blur-sm shadow-xl">
                  <h3 className="text-md font-bold mb-4 flex items-center gap-2">
                    <Award className="w-5 h-5 text-amber-400" />
                    AI Career & Interview Strategy
                  </h3>

                  <div className="flex flex-wrap gap-2 mb-4 border-b border-slate-700 pb-3">
                    {[
                      { id: 'summary', label: 'Executive Summary' },
                      { id: 'interview', label: 'Interview Prep' },
                      { id: 'projects', label: 'Project Ideas' },
                      { id: 'certifications', label: 'Certifications' },
                      { id: 'portfolio', label: 'Portfolio / Resume' },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveAdviceTab(tab.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                          activeAdviceTab === tab.id
                            ? 'bg-blue-600 text-white shadow-md'
                            : 'bg-slate-900/60 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  <div className="text-sm text-slate-300 space-y-2">
                    {activeAdviceTab === 'summary' && (
                      <p className="leading-relaxed bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                        {analysis.career_advice.executive_summary ||
                          'Comprehensive analysis of candidate career alignment.'}
                      </p>
                    )}
                    {activeAdviceTab === 'interview' && (
                      <ul className="list-disc list-inside space-y-2 bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                        {(analysis.career_advice.interview_preparation_advice || []).map(
                          (tip, idx) => (
                            <li key={idx} className="text-xs text-slate-300">
                              {tip}
                            </li>
                          )
                        )}
                      </ul>
                    )}
                    {activeAdviceTab === 'projects' && (
                      <ul className="list-disc list-inside space-y-2 bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                        {(analysis.career_advice.project_suggestions || []).map(
                          (proj, idx) => (
                            <li key={idx} className="text-xs text-slate-300">
                              {proj}
                            </li>
                          )
                        )}
                      </ul>
                    )}
                    {activeAdviceTab === 'certifications' && (
                      <ul className="list-disc list-inside space-y-2 bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                        {(analysis.career_advice.certification_suggestions || []).map(
                          (cert, idx) => (
                            <li key={idx} className="text-xs text-slate-300">
                              {cert}
                            </li>
                          )
                        )}
                      </ul>
                    )}
                    {activeAdviceTab === 'portfolio' && (
                      <div className="space-y-3 bg-slate-900/50 p-4 rounded-lg border border-slate-800 text-xs">
                        <div>
                          <strong className="text-emerald-400 block mb-1">
                            Portfolio Improvements:
                          </strong>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {(analysis.career_advice.portfolio_improvements || []).map(
                              (p, idx) => (
                                <li key={idx}>{p}</li>
                              )
                            )}
                          </ul>
                        </div>
                        <div>
                          <strong className="text-blue-400 block mb-1">
                            Resume Refinements:
                          </strong>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {(analysis.career_advice.resume_improvements || []).map(
                              (r, idx) => (
                                <li key={idx}>{r}</li>
                              )
                            )}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-12 text-center flex flex-col items-center justify-center h-full min-h-[400px]">
              <Briefcase className="w-12 h-12 text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-300">
                No Job Match Evaluated Yet
              </h3>
              <p className="text-sm text-slate-500 max-w-md mt-2">
                Paste a target job description on the left to evaluate your Digital Twin fit,
                identify skill gaps, and receive a customized salary and learning plan.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* History Modal / Drawer */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto flex flex-col">
            <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <History className="w-5 h-5 text-blue-400" />
                Previous Job Analyses
              </h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-medium"
              >
                Close &times;
              </button>
            </div>

            <div className="space-y-4 flex-grow">
              {history.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">
                  No previous job analyses saved yet.
                </p>
              ) : (
                history.map((item, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      analysis && analysis.id === item.id
                        ? 'bg-slate-800 border-emerald-500/50 shadow-md'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                    onClick={() => {
                      setAnalysis(item);
                      setShowHistory(false);
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold text-sm text-slate-200">
                          {item.job_title}
                        </h4>
                        <p className="text-xs text-slate-400">
                          {item.company || 'Unknown Company'} • {item.overall_job_match_score}% Match
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(item.id);
                        }}
                        className="text-slate-500 hover:text-red-400 p-1"
                        title="Delete evaluation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
