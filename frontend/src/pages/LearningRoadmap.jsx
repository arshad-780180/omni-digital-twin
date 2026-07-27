import React, { useState, useEffect } from 'react';
import {
  generateRoadmap,
  getLatestRoadmap,
  getRoadmapHistory,
  completeMilestone,
  recalculateRoadmap,
  deleteRoadmap,
} from '../services/learning';
import {
  BookOpen,
  Loader2,
  CheckCircle2,
  Circle,
  TrendingUp,
  Award,
  Clock,
  Sparkles,
  Target,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Trash2,
  RefreshCw,
  FolderGit2,
  Calendar,
  Zap,
  AlertTriangle,
  Briefcase,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LearningRoadmap() {
  const [activeTab, setActiveTab] = useState('phases'); // 'phases' | 'projects' | 'resources' | 'schedule' | 'history'
  const [roadmap, setRoadmap] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState('');
  const [successToast, setSuccessToast] = useState('');

  // Setup Generator Form
  const [targetRole, setTargetRole] = useState('Senior Backend Engineer');
  const [timeframeWeeks, setTimeframeWeeks] = useState(8);
  const [expandedPhases, setExpandedPhases] = useState({ 1: true, 2: true, 3: false, 4: false });

  const fetchLatest = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getLatestRoadmap();
      setRoadmap(data);
      if (data?.target_role) setTargetRole(data.target_role);
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load learning roadmap.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const data = await getRoadmapHistory();
      setHistoryData(data);
    } catch (err) {
      console.error('Failed to load roadmap history:', err);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError('');
    setSuccessToast('');
    try {
      const data = await generateRoadmap({
        target_role: targetRole,
        target_timeframe_weeks: timeframeWeeks,
      });
      setRoadmap(data);
      setSuccessToast('Personalized AI Learning Roadmap generated & Digital Twin Memory linked!');
      setActiveTab('phases');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate AI learning roadmap.');
    } finally {
      setGenerating(false);
    }
  };

  const handleCompleteMilestone = async (milestoneId, isCompleted) => {
    if (isCompleted || !roadmap) return;
    try {
      const updated = await completeMilestone(roadmap.id, {
        milestone_id: milestoneId,
      });
      setRoadmap(updated);
      setSuccessToast(`Milestone '${milestoneId}' completed! Career readiness score & Digital Twin Memory updated.`);
      setTimeout(() => setSuccessToast(''), 5000);
    } catch (err) {
      setError('Failed to update milestone status.');
    }
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    setError('');
    try {
      const updated = await recalculateRoadmap();
      setRoadmap(updated);
      setSuccessToast('Roadmap recalculated against latest Digital Twin Memory!');
      setTimeout(() => setSuccessToast(''), 4000);
    } catch (err) {
      setError('Failed to recalculate roadmap.');
    } finally {
      setRecalculating(false);
    }
  };

  const handleDeleteRoadmap = async (id) => {
    if (!window.confirm('Are you sure you want to delete this learning roadmap?')) return;
    try {
      await deleteRoadmap(id);
      if (roadmap && roadmap.id === id) {
        setRoadmap(null);
      }
      fetchHistory();
      setSuccessToast('Roadmap deleted.');
    } catch (err) {
      setError('Failed to delete roadmap.');
    }
  };

  const togglePhase = (phaseNum) => {
    setExpandedPhases((prev) => ({ ...prev, [phaseNum]: !prev[phaseNum] }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Header & Mentor Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md shadow-xl">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                <BookOpen className="w-6 h-6" />
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent">
                AI Personalized Learning Roadmap Engine
              </h1>
            </div>
            <p className="text-slate-400 text-sm sm:text-base max-w-2xl">
              Continuous AI Career Mentor that adapts to your Resume, GitHub, ATS, and Mock Interview progress.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {roadmap && (
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-sm font-medium border border-slate-700 transition"
              >
                <RefreshCw className={`w-4 h-4 ${recalculating ? 'animate-spin' : ''}`} />
                {recalculating ? 'Syncing...' : 'Sync Digital Twin Memory'}
              </button>
            )}
          </div>
        </div>

        {/* Generate Roadmap Wizard Bar */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 mb-8 backdrop-blur-md">
          <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row items-stretch sm:items-end gap-4">
            <div className="flex-1">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Target Role
              </label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
                required
              />
            </div>

            <div className="w-full sm:w-48">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Target Timeframe
              </label>
              <select
                value={timeframeWeeks}
                onChange={(e) => setTimeframeWeeks(Number(e.target.value))}
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 transition"
              >
                <option value={4}>4 Weeks (Intensive)</option>
                <option value={8}>8 Weeks (Standard)</option>
                <option value={12}>12 Weeks (Comprehensive)</option>
                <option value={16}>16 Weeks (Mastery)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate AI Roadmap
                </>
              )}
            </button>
          </form>
        </div>

        {/* Notifications & Error alerts */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successToast && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center gap-3 animate-fade-in">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span>{successToast}</span>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24">
            <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
            <p className="text-slate-400 font-medium">Loading AI Career Mentor roadmap...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !roadmap && (
          <div className="text-center py-20 bg-slate-900/30 border border-slate-800/80 rounded-2xl p-8 max-w-2xl mx-auto">
            <Target className="w-12 h-12 text-indigo-400 mx-auto mb-4 opacity-80" />
            <h3 className="text-xl font-bold text-white mb-2">No Active Learning Roadmap Found</h3>
            <p className="text-slate-400 text-sm mb-6">
              Enter your target role above and generate a customized, multi-phase AI learning roadmap that continuously guides your career journey.
            </p>
          </div>
        )}

        {/* Active Roadmap UI */}
        {!loading && roadmap && (
          <div>
            {/* Career Readiness Progress Gauge Bar */}
            <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800/80 rounded-2xl p-6 mb-8 shadow-xl">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Current Readiness
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-indigo-400">
                      {roadmap.current_readiness}%
                    </span>
                    <span className="text-xs text-slate-500">
                      / {roadmap.target_readiness}% target
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Milestone Progress
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-emerald-400">
                      {roadmap.progress_percentage || 0}%
                    </span>
                    <span className="text-xs text-slate-500">
                      ({roadmap.progress_summary?.completed_milestones || 0} / {roadmap.progress_summary?.total_milestones || len(roadmap.milestones || [])} completed)
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Estimated Time
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-amber-400">
                      {roadmap.estimated_completion || '8 weeks'}
                    </span>
                    <span className="text-xs text-slate-500">to job readiness</span>
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                    Skills Acquired
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-violet-400">
                      {roadmap.progress_summary?.skills_acquired_count || 0}
                    </span>
                    <span className="text-xs text-slate-500">verified in memory</span>
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold text-slate-400">
                  <span>Career Readiness Evolution</span>
                  <span>{roadmap.current_readiness}% / {roadmap.target_readiness}%</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-400 h-full rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(100, (roadmap.current_readiness / (roadmap.target_readiness || 100)) * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex flex-wrap border-b border-slate-800 mb-8 gap-2">
              {[
                { id: 'phases', label: 'Learning Phases & Milestones', icon: Award },
                { id: 'projects', label: 'Recommended Projects', icon: FolderGit2 },
                { id: 'resources', label: 'Resources & Certs', icon: BookOpen },
                { id: 'schedule', label: 'Practice Schedule', icon: Calendar },
                { id: 'history', label: 'Roadmap Analytics & History', icon: TrendingUp },
              ].map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition ${
                      active
                        ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                        : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab 1: Learning Phases & Interactive Milestones */}
            {activeTab === 'phases' && (
              <div className="space-y-6">
                {(roadmap.roadmap?.learning_phases || []).map((phase) => {
                  const isExpanded = expandedPhases[phase.phase_number] !== false;
                  const allPhaseMilestones = phase.milestones || [];
                  const completedPhaseCount = allPhaseMilestones.filter((m) => m.completed).length;
                  const totalPhaseCount = allPhaseMilestones.length;

                  return (
                    <div
                      key={phase.phase_number}
                      className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm"
                    >
                      {/* Phase Accordion Header */}
                      <div
                        onClick={() => togglePhase(phase.phase_number)}
                        className="flex items-center justify-between p-6 cursor-pointer hover:bg-slate-800/30 transition"
                      >
                        <div className="flex items-center gap-4">
                          <span className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-indigo-400">
                            {phase.phase_number}
                          </span>
                          <div>
                            <h3 className="text-lg font-bold text-white">{phase.title}</h3>
                            <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5" />
                                {phase.estimated_hours} Hours
                              </span>
                              <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                                {phase.difficulty}
                              </span>
                              <span>
                                ({completedPhaseCount} / {totalPhaseCount} milestones)
                              </span>
                            </div>
                          </div>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>

                      {/* Phase Content */}
                      {isExpanded && (
                        <div className="p-6 pt-0 border-t border-slate-800/60 space-y-6">
                          {/* Objectives & Expected Outcomes */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-sm">
                            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
                              <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                <Target className="w-4 h-4 text-indigo-400" /> Objectives
                              </h4>
                              <ul className="list-disc list-inside space-y-1 text-slate-400">
                                {phase.objectives?.map((obj, idx) => (
                                  <li key={idx}>{obj}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
                              <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-emerald-400" /> Expected Outcomes
                              </h4>
                              <ul className="list-disc list-inside space-y-1 text-slate-400">
                                {phase.expected_outcomes?.map((out, idx) => (
                                  <li key={idx}>{out}</li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          {/* Interactive Milestones Checklist */}
                          <div>
                            <h4 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                              Phase Milestones (Click to complete & update Digital Twin Memory)
                            </h4>
                            <div className="space-y-2.5">
                              {allPhaseMilestones.map((milestone) => {
                                const completed = milestone.completed;
                                return (
                                  <div
                                    key={milestone.milestone_id || milestone.title}
                                    onClick={() => handleCompleteMilestone(milestone.milestone_id || milestone.title, completed)}
                                    className={`flex items-start justify-between p-4 rounded-xl border transition cursor-pointer ${
                                      completed
                                        ? 'bg-emerald-500/10 border-emerald-500/30 text-slate-200'
                                        : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
                                    }`}
                                  >
                                    <div className="flex items-start gap-3">
                                      {completed ? (
                                        <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                                      ) : (
                                        <Circle className="w-5 h-5 text-slate-500 flex-shrink-0 mt-0.5" />
                                      )}
                                      <div>
                                        <p className={`font-semibold ${completed ? 'line-through text-slate-400' : 'text-white'}`}>
                                          {milestone.title}
                                        </p>
                                        <p className="text-xs text-slate-400 mt-1">{milestone.description}</p>
                                        {milestone.skills_unlocked?.length > 0 && (
                                          <div className="flex flex-wrap gap-1.5 mt-2">
                                            {milestone.skills_unlocked.map((sk, idx) => (
                                              <span
                                                key={idx}
                                                className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/60 text-[10px] text-slate-300"
                                              >
                                                +{sk}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    <span className="text-xs font-semibold uppercase px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                                      {milestone.category}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          {/* Phase Checkpoint Banner */}
                          {phase.checkpoint && (
                            <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs flex items-center gap-2">
                              <Zap className="w-4 h-4 flex-shrink-0 text-indigo-400" />
                              <span>
                                <strong>Checkpoint:</strong> {phase.checkpoint}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Tab 2: Project Recommendations */}
            {activeTab === 'projects' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {(roadmap.roadmap?.projects || roadmap.projects || []).map((project, idx) => (
                  <div
                    key={project.project_id || idx}
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="text-lg font-bold text-white">{project.title}</h3>
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">
                          {project.portfolio_value} Portfolio Value
                        </span>
                      </div>
                      <p className="text-slate-400 text-sm mb-4">{project.description}</p>
                    </div>

                    <div>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {(project.skills_covered || []).map((sk, skIdx) => (
                          <span
                            key={skIdx}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 font-medium"
                          >
                            {sk}
                          </span>
                        ))}
                      </div>

                      <div className="flex justify-between items-center text-xs text-slate-500 border-t border-slate-800/80 pt-3">
                        <span>Difficulty: {project.difficulty}</span>
                        <span>Time: {project.estimated_time}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 3: Curated Resources & Certifications */}
            {activeTab === 'resources' && (
              <div className="space-y-8">
                {/* Certifications Section */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Award className="w-5 h-5 text-amber-400" />
                    Recommended Industry Certifications
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {(roadmap.roadmap?.certifications || roadmap.certifications || []).map((cert, idx) => (
                      <div
                        key={cert.cert_id || idx}
                        className="bg-slate-900/50 border border-slate-800 rounded-xl p-5"
                      >
                        <span className="text-xs font-semibold uppercase text-amber-400 tracking-wider block mb-1">
                          {cert.issuer}
                        </span>
                        <h4 className="font-bold text-white mb-2">{cert.title}</h4>
                        <p className="text-xs text-slate-400 mb-3">{cert.relevance}</p>
                        <div className="flex justify-between text-xs text-slate-500">
                          <span>Difficulty: {cert.difficulty}</span>
                          <span>Priority: {cert.priority}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Curated Resources List */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-indigo-400" />
                    Curated Documentation, Courses & System Design
                  </h3>
                  <div className="space-y-3">
                    {(roadmap.roadmap?.resources || roadmap.resources || []).map((res, idx) => (
                      <div
                        key={res.resource_id || idx}
                        className="flex items-center justify-between p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition"
                      >
                        <div className="flex items-center gap-4">
                          <span className="px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 font-semibold">
                            {res.type}
                          </span>
                          <div>
                            <h4 className="font-bold text-white text-sm">{res.title}</h4>
                            <span className="text-xs text-slate-500">
                              Priority: {res.priority} • Difficulty: {res.difficulty}
                            </span>
                          </div>
                        </div>
                        {res.url && (
                          <a
                            href={res.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                          >
                            <span>Open</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: Practice Schedule & Weekly Planner */}
            {activeTab === 'schedule' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-400" />
                    Weekly Coding & Study Routine
                  </h3>
                  <ul className="space-y-3 text-sm text-slate-300">
                    {(roadmap.roadmap?.practice_schedule || []).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <Circle className="w-2 h-2 text-indigo-500 mt-2 flex-shrink-0 fill-indigo-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <Briefcase className="w-5 h-5 text-violet-400" />
                    Mock Interview Preparation
                  </h3>
                  <ul className="space-y-3 text-sm text-slate-300">
                    {(roadmap.roadmap?.mock_interview_schedule || []).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <Circle className="w-2 h-2 text-violet-500 mt-2 flex-shrink-0 fill-violet-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-emerald-400" />
                    Revision & Consolidation Plan
                  </h3>
                  <ul className="space-y-3 text-sm text-slate-300">
                    {(roadmap.roadmap?.revision_plan || []).map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <Circle className="w-2 h-2 text-emerald-500 mt-2 flex-shrink-0 fill-emerald-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Tab 5: Analytics & Roadmap History */}
            {activeTab === 'history' && (
              <div className="space-y-8">
                {/* Analytics Growth Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
                    <span className="text-xs uppercase text-slate-400 block mb-1">
                      Career Readiness Growth
                    </span>
                    <span className="text-3xl font-extrabold text-emerald-400">
                      +{roadmap.analytics?.readiness_growth || 0}%
                    </span>
                  </div>

                  <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
                    <span className="text-xs uppercase text-slate-400 block mb-1">
                      Learning Velocity
                    </span>
                    <span className="text-3xl font-extrabold text-indigo-400">
                      {roadmap.analytics?.learning_velocity || 0}
                    </span>
                    <span className="text-xs text-slate-500 ml-1">milestones/week</span>
                  </div>

                  <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
                    <span className="text-xs uppercase text-slate-400 block mb-1">
                      Projects Completed
                    </span>
                    <span className="text-3xl font-extrabold text-violet-400">
                      {roadmap.analytics?.projects_completed_count || 0}
                    </span>
                  </div>
                </div>

                {/* History Archive Table */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Historical Learning Roadmaps Archive</h3>
                  <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                          <th className="p-4">Target Role</th>
                          <th className="p-4">Current -> Target</th>
                          <th className="p-4">Progress</th>
                          <th className="p-4">Created Date</th>
                          <th className="p-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {historyData?.history?.map((item) => (
                          <tr key={item.id} className="hover:bg-slate-800/30 transition">
                            <td className="p-4 font-semibold text-white">{item.target_role}</td>
                            <td className="p-4 text-slate-300">
                              {item.current_readiness}% &rarr; {item.target_readiness}%
                            </td>
                            <td className="p-4 text-emerald-400 font-bold">
                              {item.progress_percentage}%
                            </td>
                            <td className="p-4 text-slate-500 text-xs">
                              {new Date(item.created_at).toLocaleDateString()}
                            </td>
                            <td className="p-4 text-right">
                              <button
                                onClick={() => handleDeleteRoadmap(item.id)}
                                className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
