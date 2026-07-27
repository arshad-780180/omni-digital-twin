import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Brain,
  Sparkles,
  RefreshCw,
  Clock,
  Award,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Shield,
  Briefcase,
  Code,
  FileText,
  Github,
  Compass,
  ArrowLeft,
} from 'lucide-react';
import {
  getDigitalTwinMemory,
  getDigitalTwinSummary,
  getDigitalTwinTimeline,
  rebuildDigitalTwinMemory,
} from '../services/twin';

export default function DigitalTwin() {
  const [memory, setMemory] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [memData, sumData, timeData] = await Promise.all([
        getDigitalTwinMemory(),
        getDigitalTwinSummary(),
        getDigitalTwinTimeline(),
      ]);
      setMemory(memData);
      setSummary(sumData);
      setTimeline(timeData || []);
    } catch (err) {
      setError('Failed to load Digital Twin memory. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRebuild = async () => {
    setRebuilding(true);
    setError('');
    setSuccessMsg('');
    try {
      const newMemory = await rebuildDigitalTwinMemory();
      setMemory(newMemory);
      const [sumData, timeData] = await Promise.all([
        getDigitalTwinSummary(),
        getDigitalTwinTimeline(),
      ]);
      setSummary(sumData);
      setTimeline(timeData || []);
      setSuccessMsg('Digital Twin Memory successfully rebuilt from historical analyses!');
    } catch (err) {
      setError('Failed to rebuild memory from history.');
      console.error(err);
    } finally {
      setRebuilding(false);
    }
  };

  const getModuleBadge = (mod) => {
    switch (mod) {
      case 'resume':
        return { bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20', icon: FileText, label: 'Resume' };
      case 'github':
        return { bg: 'bg-purple-500/10 text-purple-400 border-purple-500/20', icon: Github, label: 'GitHub' };
      case 'career':
        return { bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', icon: Compass, label: 'Career' };
      case 'ats':
        return { bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20', icon: Award, label: 'ATS' };
      case 'job_matching':
        return { bg: 'bg-teal-500/10 text-teal-400 border-teal-500/20', icon: Briefcase, label: 'Job Match' };
      default:
        return { bg: 'bg-slate-700/50 text-slate-300 border-slate-600', icon: Brain, label: 'System' };
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="px-8 py-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 backdrop-blur-md sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-tr from-blue-500 to-indigo-500 rounded-xl shadow-lg shadow-blue-500/20">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400">
                AI Digital Twin Memory Engine
              </h1>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleRebuild}
            disabled={rebuilding || loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-sm font-medium transition-all shadow-sm hover:shadow-md disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${rebuilding ? 'animate-spin' : ''}`} />
            <span>{rebuilding ? 'Rebuilding Memory...' : 'Rebuild from History'}</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow p-8 max-w-7xl mx-auto w-full space-y-8">
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-400 text-sm animate-pulse">Loading Digital Twin Persistent Memory...</p>
          </div>
        ) : !memory ? (
          <div className="text-center py-16 bg-slate-800/40 rounded-2xl border border-slate-800">
            <Brain className="w-12 h-12 text-slate-500 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-slate-300">No Memory Found</h3>
            <p className="text-sm text-slate-400 mt-1 mb-6">
              Your Digital Twin is ready to start learning from your career activities.
            </p>
            <button
              onClick={handleRebuild}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Initialize Memory
            </button>
          </div>
        ) : (
          <>
            {/* Executive Summary Card */}
            {summary && (
              <div className="bg-gradient-to-br from-slate-800/80 via-slate-800/50 to-indigo-900/20 border border-slate-700/80 rounded-2xl p-6 md:p-8 shadow-xl backdrop-blur-md relative overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -z-10 pointer-events-none"></div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-700/60">
                  <div>
                    <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">
                      <Sparkles className="w-4 h-4" />
                      <span>Executive Career Synthesis</span>
                    </div>
                    <h2 className="text-2xl md:text-3xl font-bold text-white">
                      {summary.executive_summary || memory.current_role || 'Developer Profile'}
                    </h2>
                    <p className="text-slate-300 text-sm mt-1">
                      {summary.career_identity || 'Evolving Software Professional'}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="bg-slate-900/60 border border-slate-700 px-4 py-2.5 rounded-xl text-center">
                      <span className="text-xs text-slate-400 block">Career Stage</span>
                      <span className="text-sm font-semibold text-emerald-400">
                        {summary.career_stage || 'Mid-Level'}
                      </span>
                    </div>

                    <div className="bg-slate-900/60 border border-slate-700 px-4 py-2.5 rounded-xl text-center">
                      <span className="text-xs text-slate-400 block">Memory Version</span>
                      <span className="text-sm font-semibold text-blue-400">
                        v{memory.metadata?.version || 1}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Key Strengths */}
                  <div className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-5">
                    <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                      <Award className="w-4 h-4 text-emerald-400" />
                      <span>Key Career Strengths</span>
                    </h4>
                    <ul className="space-y-2">
                      {(summary.top_strengths || memory.career_strengths || []).slice(0, 4).map((str, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Primary Domains */}
                  <div className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-5">
                    <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                      <Briefcase className="w-4 h-4 text-blue-400" />
                      <span>Target Roles & Domains</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {(summary.primary_domains || memory.target_roles || []).slice(0, 6).map((role, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20 font-medium"
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Recommended Next Step */}
                  <div className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-5">
                    <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-amber-400" />
                      <span>Recommended Next Step</span>
                    </h4>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {summary.recommended_next_step ||
                        'Continue expanding technical skills and running targeted ATS and job matching evaluations.'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Skills & Competency Matrix */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Core Skills Card */}
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Code className="w-5 h-5 text-indigo-400" />
                    <span>Mastered Competencies ({memory.core_skills?.length || 0})</span>
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto pr-1">
                  {(memory.core_skills || []).map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900/80 text-slate-200 border border-slate-700 hover:border-indigo-500/40 transition-colors"
                    >
                      {skill}
                    </span>
                  ))}
                  {(memory.core_skills || []).length === 0 && (
                    <p className="text-xs text-slate-400">No core skills recorded yet. Upload a resume or analyze GitHub.</p>
                  )}
                </div>
              </div>

              {/* Missing / Target Skills Card */}
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Shield className="w-5 h-5 text-amber-400" />
                    <span>Growth & Skill Gaps ({memory.missing_skills?.length || 0})</span>
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto pr-1">
                  {(memory.missing_skills || []).map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20"
                    >
                      {skill}
                    </span>
                  ))}
                  {(memory.missing_skills || []).length === 0 && (
                    <p className="text-xs text-slate-400">No skill gaps identified yet.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Memory Evolution Timeline & Module Summaries */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Timeline Section */}
              <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700/80 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-400" />
                    <h3 className="text-lg font-semibold text-white">Memory Evolution Timeline</h3>
                  </div>
                  <span className="text-xs text-slate-400">
                    {timeline.length} Recorded Events
                  </span>
                </div>

                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-700">
                  {timeline.slice().reverse().map((event, index) => {
                    const badge = getModuleBadge(event.source_module);
                    const IconComponent = badge.icon;
                    return (
                      <div key={index} className="relative group">
                        <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-slate-900 border-2 border-indigo-400 flex items-center justify-center"></div>
                        <div className="bg-slate-900/60 border border-slate-700/70 rounded-xl p-4 transition-all hover:border-slate-600">
                          <div className="flex items-center justify-between gap-2 mb-1.5">
                            <span className="text-xs font-semibold text-slate-300">{event.event}</span>
                            <span
                              className={`px-2 py-0.5 rounded-md text-[10px] font-medium border flex items-center gap-1 ${badge.bg}`}
                            >
                              <IconComponent className="w-3 h-3" />
                              <span>{badge.label}</span>
                            </span>
                          </div>
                          {event.details && (
                            <p className="text-xs text-slate-400 mb-2">{event.details}</p>
                          )}
                          <div className="text-[11px] text-slate-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            <span>{event.date}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Module Histories Section */}
              <div className="space-y-6">
                {/* ATS History Summary */}
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-6">
                  <h4 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <Award className="w-4 h-4 text-amber-400" />
                    <span>ATS Optimization History</span>
                  </h4>
                  <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                    {(memory.ats_history_summary || []).length === 0 ? (
                      <p className="text-xs text-slate-400">No ATS checks recorded.</p>
                    ) : (
                      (memory.ats_history_summary || []).map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-slate-900/70 border border-slate-700 text-xs text-slate-300"
                        >
                          {item}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Job Matching Summary */}
                <div className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-6">
                  <h4 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-emerald-400" />
                    <span>Job Matching History</span>
                  </h4>
                  <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                    {(memory.job_matching_summary || []).length === 0 ? (
                      <p className="text-xs text-slate-400">No job matching checks recorded.</p>
                    ) : (
                      (memory.job_matching_summary || []).map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-slate-900/70 border border-slate-700 text-xs text-slate-300"
                        >
                          {item}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
