import React, { useState, useEffect } from 'react';
import {
  Activity,
  Award,
  TrendingUp,
  Target,
  CheckCircle2,
  AlertCircle,
  FileText,
  Download,
  ShieldCheck,
  Zap,
  BookOpen,
  Briefcase,
  Users,
  Clock,
  ArrowUpRight,
  RefreshCw,
  Loader2,
  Layers,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { getDashboardSummary, downloadReport } from '../services/analytics';

const AnalyticsDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportingType, setExportingType] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, matrix, timeline

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load Executive Analytics Dashboard. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleExport = async (reportType) => {
    setExportingType(reportType);
    try {
      await downloadReport(reportType);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExportingType(null);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'from-emerald-500 to-teal-400 text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 70) return 'from-blue-500 to-indigo-400 text-blue-400 border-blue-500/30 bg-blue-500/10';
    if (score >= 50) return 'from-amber-500 to-yellow-400 text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'from-rose-500 to-red-400 text-rose-400 border-rose-500/30 bg-rose-500/10';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Excellent':
        return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
      case 'Strong':
        return 'bg-blue-500/20 text-blue-300 border border-blue-500/40';
      case 'Moderate':
        return 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
      default:
        return 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <h2 className="text-xl font-semibold mb-2">Aggregating OMNI Career Intelligence</h2>
        <p className="text-slate-400 text-sm max-w-md text-center">
          Synthesizing Profile, Resume, GitHub, ATS, Job Matches, Interviews, and Learning Roadmaps into your Executive Career Health Audit...
        </p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6">
        <AlertCircle className="w-12 h-12 text-rose-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Dashboard Aggregation Notice</h2>
        <p className="text-slate-400 text-sm mb-6">{error || 'No analytics summary available.'}</p>
        <button
          onClick={fetchDashboard}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-semibold transition-all flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Retry Aggregation
        </button>
      </div>
    );
  }

  const {
    career_health_score: healthScore,
    career_readiness_score: readinessScore,
    ats_score: atsScore,
    job_match_score: jobMatchScore,
    interview_score: interviewScore,
    learning_progress: learningProgress,
    digital_twin_confidence: confidence,
    career_goal_progress: goalProgress,
    insights,
    skill_matrix: skillMatrix,
    timeline,
    career_analytics: careerAnalytics,
    ats_analytics: atsAnalytics,
    job_match_analytics: jobMatchAnalytics,
    interview_analytics: interviewAnalytics,
  } = summary;

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-16">
      {/* Dashboard Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                OMNI v1.0 Production
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Analytics & Career Intelligence Dashboard</h1>
            <p className="text-slate-400 text-xs">
              Executive command center answering: "How close is this user to achieving their target career?"
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => handleExport('career')}
              disabled={!!exportingType}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              {exportingType === 'career' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
              ) : (
                <Download className="w-3.5 h-3.5 text-blue-400" />
              )}
              <span>Career Report (PDF)</span>
            </button>
            <button
              onClick={() => handleExport('summary')}
              disabled={!!exportingType}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              {exportingType === 'summary' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              ) : (
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
              )}
              <span>Analytics Summary</span>
            </button>
            <button
              onClick={fetchDashboard}
              className="p-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-white transition-all shadow-lg shadow-blue-600/20"
              title="Refresh Analytics"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-6 flex gap-4 border-t border-slate-800/80 text-sm">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3 font-semibold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Executive Command Center</span>
          </button>
          <button
            onClick={() => setActiveTab('matrix')}
            className={`py-3 font-semibold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'matrix'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>11-Skill Growth Matrix</span>
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`py-3 font-semibold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'timeline'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Chronological Career Timeline</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 pt-8 space-y-8">
        {activeTab === 'overview' && (
          <>
            {/* Top Row: Executive Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Overall Career Health Score */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Overall Career Health
                  </span>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${getStatusBadge(healthScore.status)}`}>
                    {healthScore.status}
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black text-white">{healthScore.overall_score}</span>
                  <span className="text-sm font-semibold text-slate-400">/ 100</span>
                </div>
                <div className="w-full bg-slate-700/60 h-2 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-emerald-400"
                    style={{ width: `${healthScore.overall_score}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400 flex items-center justify-between">
                  <span>Digital Twin Confidence:</span>
                  <span className="font-semibold text-emerald-400">{confidence}%</span>
                </p>
              </div>

              {/* Card 2: Career Readiness & ATS */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-md flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                    Core Readiness & ATS Match
                  </span>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Readiness</span>
                      <span className="text-xl font-bold text-blue-400">{readinessScore}%</span>
                    </div>
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">ATS Score</span>
                      <span className="text-xl font-bold text-indigo-400">{atsScore}%</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>ATS Keyword Coverage:</span>
                  <span className="font-semibold text-white">{atsAnalytics.keyword_coverage}%</span>
                </div>
              </div>

              {/* Card 3: Job Match & Interview Performance */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-md flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                    Role Fit & Mock Interview
                  </span>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Job Match</span>
                      <span className="text-xl font-bold text-emerald-400">{jobMatchScore}%</span>
                    </div>
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Interview</span>
                      <span className="text-xl font-bold text-teal-400">{interviewScore}%</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Top Role:</span>
                  <span className="font-semibold text-white truncate max-w-[140px]">{jobMatchAnalytics.best_matching_role}</span>
                </div>
              </div>

              {/* Card 4: Learning Roadmap & Goal Progress */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-md flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                    Learning Roadmap Velocity
                  </span>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Roadmap</span>
                      <span className="text-xl font-bold text-purple-400">{Math.round(learningProgress)}%</span>
                    </div>
                    <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Goal Fit</span>
                      <span className="text-xl font-bold text-pink-400">{goalProgress}%</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Est. Goal Target:</span>
                  <span className="font-semibold text-purple-300">{careerAnalytics.estimated_goal_date}</span>
                </div>
              </div>
            </div>

            {/* AI Executive Insights & Recommendations Panel */}
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-blue-500/30 rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <h2 className="text-lg font-bold text-white">AI Executive Career Synthesis</h2>
                    <span className="text-xs bg-slate-700/60 text-slate-300 px-2.5 py-0.5 rounded-full border border-slate-600">
                      {insights.ai_generated ? 'Gemini AI Validated' : 'Deterministic Rule Fallback'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Comprehensive synthesis of strengths, skill gaps, trajectory momentum, and recommended next steps.
                  </p>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl px-4 py-2 text-center">
                  <span className="text-xs text-slate-400 block">Estimated Readiness Profile</span>
                  <span className="text-sm font-bold text-blue-300">{insights.estimated_readiness}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* Strengths */}
                <div className="bg-slate-900/50 border border-slate-700/60 rounded-2xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-3 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Top Demonstrated Strengths</span>
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {insights.current_strengths.map((s, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Weakest Areas */}
                <div className="bg-slate-900/50 border border-slate-700/60 rounded-2xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-3 flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4" />
                    <span>Areas Requiring Attention</span>
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {insights.weakest_areas.map((w, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Biggest Improvement & Risks */}
                <div className="bg-slate-900/50 border border-slate-700/60 rounded-2xl p-4 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-2 flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4" />
                      <span>Biggest Improvement</span>
                    </h3>
                    <p className="text-xs text-slate-300 mb-4 bg-blue-500/10 p-2.5 rounded-xl border border-blue-500/20">
                      {insights.biggest_improvement}
                    </p>
                  </div>

                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 mb-2 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Career Risk Notice</span>
                    </h3>
                    <p className="text-xs text-rose-300/90">
                      {insights.career_risks[0] || 'Continued portfolio updates required to maintain competitive edge.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Recommended Next Action Banner */}
              <div className="bg-gradient-to-r from-blue-600/20 via-indigo-600/20 to-purple-600/20 border border-blue-500/40 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shrink-0">
                    <Zap className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
                      Recommended Next Action
                    </span>
                    <p className="text-sm font-medium text-white">{insights.recommended_next_action}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleExport('progress')}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-xs font-semibold whitespace-nowrap transition-all"
                >
                  Download Progress Report
                </button>
              </div>
            </div>

            {/* Visual Charts & Dimension Trend Breakdowns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Chart: Multi-Dimension Competency Bar Trajectories */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 backdrop-blur-md">
                <h3 className="text-base font-bold text-white mb-4 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span>Multi-Dimension Competency Comparison</span>
                  </span>
                  <span className="text-xs text-slate-400 font-normal">v1.0 Normalized Scores</span>
                </h3>

                <div className="space-y-4">
                  {/* Readiness */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-300">Career Readiness Engine</span>
                      <span className="text-blue-400">{readinessScore} / 100</span>
                    </div>
                    <div className="w-full bg-slate-700/60 h-3 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${readinessScore}%` }} />
                    </div>
                  </div>

                  {/* ATS */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-300">ATS Resume Optimization</span>
                      <span className="text-indigo-400">{atsScore} / 100</span>
                    </div>
                    <div className="w-full bg-slate-700/60 h-3 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500" style={{ width: `${atsScore}%` }} />
                    </div>
                  </div>

                  {/* Job Match */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-300">Job Matching Fit Score</span>
                      <span className="text-emerald-400">{jobMatchScore} / 100</span>
                    </div>
                    <div className="w-full bg-slate-700/60 h-3 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${jobMatchScore}%` }} />
                    </div>
                  </div>

                  {/* Interview */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-300">Mock Interview Performance</span>
                      <span className="text-teal-400">{interviewScore} / 100</span>
                    </div>
                    <div className="w-full bg-slate-700/60 h-3 rounded-full overflow-hidden">
                      <div className="h-full bg-teal-500" style={{ width: `${interviewScore}%` }} />
                    </div>
                  </div>

                  {/* Learning Roadmap */}
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-300">Learning Roadmap Completion</span>
                      <span className="text-purple-400">{Math.round(learningProgress)}%</span>
                    </div>
                    <div className="w-full bg-slate-700/60 h-3 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500" style={{ width: `${learningProgress}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Chart: Interview Dimensions & Keyword Gaps */}
              <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 backdrop-blur-md flex flex-col justify-between">
                <div>
                  <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-indigo-400" />
                    <span>Interview Analytics & Top Missing Skills</span>
                  </h3>

                  <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Interview Success Rate</span>
                      <span className="text-lg font-bold text-emerald-400">
                        {interviewAnalytics.interview_success_rate}%
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-700/50">
                      <span className="text-xs text-slate-400 block">Most Improved Topic</span>
                      <span className="text-xs font-bold text-blue-300 block truncate">
                        {interviewAnalytics.most_improved_topic}
                      </span>
                    </div>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-slate-400 block mb-2">
                      Top Missing Skills Across Target Job Descriptions:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {atsAnalytics.top_missing_skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
                  <span>ATS Keyword Coverage:</span>
                  <span className="text-white font-bold">{atsAnalytics.keyword_coverage}% Verified</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Tab 2: 11-Skill Growth Matrix */}
        {activeTab === 'matrix' && (
          <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">11-Skill Engineering Competency Matrix</h2>
                <p className="text-xs text-slate-400">
                  Visual matrix tracking Current Level, Growth Trend, and Target Level across required OMNI engineering skills.
                </p>
              </div>
              <span className="text-xs bg-blue-500/10 text-blue-400 px-3 py-1.5 rounded-xl border border-blue-500/20 font-semibold">
                {skillMatrix.length} Verified Competencies
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-700 text-xs font-bold uppercase tracking-wider text-slate-400">
                    <th className="py-3 px-4">Skill / Technology</th>
                    <th className="py-3 px-4">Current Level</th>
                    <th className="py-3 px-4">Growth Trend</th>
                    <th className="py-3 px-4">Target Level</th>
                    <th className="py-3 px-4">Proficiency Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/60 text-sm">
                  {skillMatrix.map((skill, idx) => (
                    <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400" />
                        <span>{skill.skill_name}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                            skill.current_level === 'Advanced' || skill.current_level === 'Expert'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : skill.current_level === 'Intermediate'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}
                        >
                          {skill.current_level}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{skill.growth_trend}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-xs font-bold text-indigo-300 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20">
                          {skill.target_level}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 w-48">
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500"
                              style={{ width: `${skill.score}%` }}
                            />
                          </div>
                          <span className="text-xs font-bold text-slate-400">{skill.score}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Chronological Career Timeline */}
        {activeTab === 'timeline' && (
          <div className="bg-slate-800/60 border border-slate-700/80 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Chronological Career Evolution Timeline</h2>
                <p className="text-xs text-slate-400">
                  Living chronological history tracking every milestone, audit, and career health increase across OMNI.
                </p>
              </div>
              <button
                onClick={() => handleExport('timeline')}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
              >
                <Download className="w-3.5 h-3.5 text-blue-400" />
                <span>Export Timeline Report</span>
              </button>
            </div>

            <div className="relative border-l-2 border-slate-700 ml-4 pl-6 space-y-8">
              {timeline.map((evt, idx) => (
                <div key={evt.event_id || idx} className="relative group">
                  <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-blue-500 border-4 border-slate-900 group-hover:scale-125 transition-transform" />
                  <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-4 hover:border-slate-600 transition-all">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
                        {evt.event_type}
                      </span>
                      <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        +{evt.impact_score} Career Health Pts
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-white mb-1">{evt.title}</h4>
                    <p className="text-xs text-slate-300 mb-2">{evt.description}</p>
                    <span className="text-[11px] text-slate-500">
                      {new Date(evt.timestamp).toLocaleString()} • Source: {evt.module_source}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AnalyticsDashboard;
