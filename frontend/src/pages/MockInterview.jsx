import React, { useState, useEffect } from 'react';
import {
  startInterview,
  submitInterviewAnswer,
  finishInterview,
  getInterviewHistory,
  deleteInterview,
} from '../services/interview';
import {
  Bot,
  Loader2,
  ChevronLeft,
  ArrowRight,
  CheckCircle2,
  MessageSquare,
  Target,
  Award,
  TrendingUp,
  Clock,
  Sparkles,
  AlertTriangle,
  BookOpen,
  Trash2,
  RefreshCw,
  HelpCircle,
  Briefcase,
  Building2,
  Sliders,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function MockInterview() {
  const [activeTab, setActiveTab] = useState('interview'); // 'interview' | 'history'
  const [step, setStep] = useState(1); // 1: Setup, 2: Q&A, 3: Results
  const [status, setStatus] = useState('idle'); // 'idle' | 'generating' | 'evaluating' | 'finishing' | 'error'
  const [errorMessage, setErrorMessage] = useState('');

  // Setup form
  const [role, setRole] = useState('');
  const [company, setCompany] = useState('');
  const [difficulty, setDifficulty] = useState('Medium');
  const [interviewType, setInterviewType] = useState('Technical');
  const [questionCount, setQuestionCount] = useState(5);

  // Active session state
  const [session, setSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [latestEvaluation, setLatestEvaluation] = useState(null);
  const [showIdealAnswer, setShowIdealAnswer] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);

  // History & Trends state
  const [historyData, setHistoryData] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Timer effect
  useEffect(() => {
    let interval = null;
    if (step === 2 && status === 'idle' && !latestEvaluation) {
      interval = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [step, status, latestEvaluation]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getInterviewHistory();
      setHistoryData(data);
    } catch (err) {
      console.error('Failed to load interview history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  const handleStart = async (e) => {
    e.preventDefault();
    if (!role.trim()) return;

    setStatus('generating');
    setErrorMessage('');
    try {
      const data = await startInterview({
        role: role.trim(),
        company: company.trim(),
        difficulty,
        interview_type: interviewType,
        question_count: Number(questionCount),
      });
      setSession(data);
      setStep(2);
      setCurrentQuestionIndex(0);
      setCurrentAnswer('');
      setLatestEvaluation(null);
      setShowIdealAnswer(false);
      setTimerSeconds(0);
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setErrorMessage(
        err.response?.data?.detail || 'Failed to start AI Mock Interview. Please check backend.'
      );
    }
  };

  const handleAnswerSubmit = async () => {
    if (!currentAnswer.trim() || !session) return;

    setStatus('evaluating');
    setErrorMessage('');
    const qObj = session.questions[currentQuestionIndex];
    const qId = qObj?.question_id || String(currentQuestionIndex + 1);

    try {
      const updatedSession = await submitInterviewAnswer(session.id, {
        question_id: qId,
        content: currentAnswer.trim(),
      });
      setSession(updatedSession);

      // Find newest evaluation
      const evalMatch = updatedSession.evaluations?.find((e) => e.question_id === qId);
      setLatestEvaluation(
        evalMatch ||
          updatedSession.evaluations?.[updatedSession.evaluations.length - 1] ||
          null
      );
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setErrorMessage(
        err.response?.data?.detail || 'Failed to evaluate answer.'
      );
    }
  };

  const handleNextQuestion = async () => {
    if (!session) return;
    if (currentQuestionIndex < session.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setCurrentAnswer('');
      setLatestEvaluation(null);
      setShowIdealAnswer(false);
      setTimerSeconds(0);
    } else {
      // Complete interview
      setStatus('finishing');
      setErrorMessage('');
      try {
        const finalSession = await finishInterview(session.id);
        setSession(finalSession);
        setStep(3);
        setStatus('idle');
      } catch (err) {
        setStatus('error');
        setErrorMessage(
          err.response?.data?.detail || 'Failed to finalize interview report.'
        );
      }
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteInterview(sessionId);
      await loadHistory();
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const formatTimer = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const getDifficultyBadge = (diff) => {
    if (diff === 'Hard')
      return 'bg-red-500/20 text-red-300 border border-red-500/30';
    if (diff === 'Easy')
      return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
    return 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 65) return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    return 'text-red-400 bg-red-500/10 border-red-500/30';
  };

  const currentQ = session?.questions?.[currentQuestionIndex];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-16">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between sticky top-0 z-10 bg-slate-900/90 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="p-2 hover:bg-slate-800 rounded-full transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div className="text-xl font-bold flex items-center gap-2">
            <Bot className="w-6 h-6 text-blue-400" />
            <span>AI Interview Coach</span>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="flex bg-slate-800/80 p-1 rounded-full border border-slate-700/60 text-sm">
          <button
            onClick={() => setActiveTab('interview')}
            className={`px-4 py-1.5 rounded-full font-medium transition-all ${
              activeTab === 'interview'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Mock Interview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-1.5 rounded-full font-medium transition-all flex items-center gap-1.5 ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>History & Trends</span>
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 md:p-8 mt-4">
        {activeTab === 'history' ? (
          /* --- TAB: HISTORY & TRENDS --- */
          <div className="space-y-8 animate-in fade-in duration-300">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Interview Performance Analytics
              </h2>
              <p className="text-slate-400 text-sm">
                Track your mock interview progress, score trajectories, and weakest areas over time.
              </p>
            </div>

            {loadingHistory ? (
              <div className="flex flex-col items-center justify-center py-24 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-3" />
                <span>Loading interview trends...</span>
              </div>
            ) : !historyData || historyData.total_interviews === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700/80 rounded-2xl p-12 text-center">
                <Award className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-1">
                  No Mock Interviews Yet
                </h3>
                <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto">
                  Complete your first mock interview to unlock AI trend analytics, score trajectories, and learning priorities.
                </p>
                <button
                  onClick={() => setActiveTab('interview')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-full shadow-lg transition-all"
                >
                  Start Your First Interview
                </button>
              </div>
            ) : (
              <>
                {/* Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Average Score
                    </div>
                    <div className="text-3xl font-extrabold text-blue-400">
                      {historyData.average_score}%
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Across {historyData.total_interviews} completed sessions
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Improvement Rate
                    </div>
                    <div className="text-3xl font-extrabold text-emerald-400">
                      +{historyData.improvement_percentage}%
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      From first to latest mock session
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Avg Duration
                    </div>
                    <div className="text-3xl font-extrabold text-purple-400">
                      {historyData.average_interview_duration} min
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Average active interview time
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Weakest Topics
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {historyData.weakest_topics?.map((topic, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-red-500/10 border border-red-500/30 text-red-300 rounded text-xs"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Score Trajectory Bar */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-400" />
                    <span>Technical & Communication Trajectory</span>
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span>Technical Proficiency Trend</span>
                        <span>Latest: {historyData.technical_trend?.slice(-1)[0] || 0}%</span>
                      </div>
                      <div className="flex items-center gap-1.5 h-6">
                        {historyData.technical_trend?.map((score, idx) => (
                          <div
                            key={idx}
                            className="flex-1 bg-blue-600/40 border border-blue-500/50 rounded flex items-center justify-center text-xs text-white font-medium"
                            style={{ height: `${maxHeightPct(score)}%` }}
                          >
                            {score}%
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span>Communication Clarity Trend</span>
                        <span>Latest: {historyData.communication_trend?.slice(-1)[0] || 0}%</span>
                      </div>
                      <div className="flex items-center gap-1.5 h-6">
                        {historyData.communication_trend?.map((score, idx) => (
                          <div
                            key={idx}
                            className="flex-1 bg-emerald-600/40 border border-emerald-500/50 rounded flex items-center justify-center text-xs text-white font-medium"
                            style={{ height: `${maxHeightPct(score)}%` }}
                          >
                            {score}%
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Historical Sessions List */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl overflow-hidden">
                  <div className="p-4 border-b border-slate-700/60 text-sm font-semibold text-slate-300">
                    Past Mock Interview Sessions ({historyData.sessions?.length || 0})
                  </div>
                  <div className="divide-y divide-slate-700/60">
                    {historyData.sessions?.map((s) => (
                      <div
                        key={s.id}
                        className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-800/40 transition-colors"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">
                              {s.role}
                            </span>
                            {s.company && (
                              <span className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded">
                                {s.company}
                              </span>
                            )}
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${getDifficultyBadge(
                                s.difficulty
                              )}`}
                            >
                              {s.difficulty}
                            </span>
                          </div>
                          <div className="text-xs text-slate-400 mt-1">
                            {s.interview_type} •{' '}
                            {new Date(s.created_at).toLocaleDateString()}{' '}
                            {new Date(s.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-lg font-bold text-blue-400">
                              {s.overall_score}%
                            </div>
                            <div className="text-xs text-slate-400">
                              Overall Score
                            </div>
                          </div>

                          <button
                            onClick={() => handleDeleteSession(s.id)}
                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                            title="Delete Session"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        ) : (
          /* --- TAB: MOCK INTERVIEW WIZARD --- */
          <>
            {/* STEP 1: SETUP FORM */}
            {step === 1 && (
              <div className="max-w-xl mx-auto mt-8 bg-slate-800/60 border border-slate-700/80 rounded-2xl p-8 backdrop-blur-sm shadow-2xl animate-in fade-in slide-in-from-bottom-4">
                <div className="w-14 h-14 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-7 h-7 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold text-center text-white mb-2">
                  Personalized Mock Interview
                </h2>
                <p className="text-slate-400 mb-8 text-sm text-center">
                  Questions are generated directly from your Digital Twin (Resume, GitHub, and ATS skills) instead of generic textbook prompts.
                </p>

                {status === 'error' && (
                  <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                    <span>{errorMessage}</span>
                  </div>
                )}

                <form onSubmit={handleStart} className="space-y-5">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
                      <Briefcase className="w-4 h-4 text-blue-400" />
                      <span>Target Role *</span>
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Senior Backend Engineer"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1.5">
                      <Building2 className="w-4 h-4 text-blue-400" />
                      <span>Target Company (Optional)</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Google, Amazon, OpenAI"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                        Difficulty
                      </label>
                      <select
                        value={difficulty}
                        onChange={(e) => setDifficulty(e.target.value)}
                        className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 text-sm"
                      >
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                        Interview Type
                      </label>
                      <select
                        value={interviewType}
                        onChange={(e) => setInterviewType(e.target.value)}
                        className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 text-sm"
                      >
                        <option value="Technical">Technical</option>
                        <option value="System Design">System Design</option>
                        <option value="Behavioral">Behavioral</option>
                        <option value="Backend">Backend</option>
                        <option value="Frontend">Frontend</option>
                        <option value="Full Stack">Full Stack</option>
                        <option value="Mixed">Mixed</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                      <span>Question Count</span>
                      <span className="text-blue-400 font-bold">{questionCount} Questions</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={questionCount}
                      onChange={(e) => setQuestionCount(e.target.value)}
                      className="w-full accent-blue-500 bg-slate-700"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={status === 'generating'}
                    className="w-full py-3.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all flex items-center justify-center gap-2 mt-4"
                  >
                    {status === 'generating' ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Generating Personalized Interview...</span>
                      </>
                    ) : (
                      <>
                        <span>Start Mock Interview</span>
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </form>
              </div>
            )}

            {/* STEP 2: INTERACTIVE QUESTION & ANSWER PANEL */}
            {step === 2 && session && currentQ && (
              <div className="space-y-6 animate-in fade-in duration-300">
                {/* Stepper Progress Bar */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-bold">
                      Question {currentQuestionIndex + 1} of {session.questions.length}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-1 rounded font-semibold ${getDifficultyBadge(
                        currentQ.difficulty || 'Medium'
                      )}`}
                    >
                      {currentQ.difficulty || 'Medium'} Difficulty
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-blue-400" />
                      <span>{formatTimer(timerSeconds)} elapsed</span>
                    </div>
                    <div className="px-2.5 py-1 bg-slate-700/60 rounded border border-slate-600/50">
                      {currentQ.category || session.interview_type}
                    </div>
                  </div>
                </div>

                {/* Progress bar line */}
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-500 h-full transition-all duration-500"
                    style={{
                      width: `${
                        ((currentQuestionIndex + 1) / session.questions.length) * 100
                      }%`,
                    }}
                  />
                </div>

                {/* Question Box */}
                <div className="bg-slate-800/70 border border-slate-700/80 rounded-2xl p-6 md:p-8 shadow-xl">
                  <div className="text-xs font-semibold uppercase tracking-wider text-blue-400 mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    <span>
                      {currentQ.generated_from || 'Generated from Digital Twin Context'}
                    </span>
                  </div>
                  <h3 className="text-xl md:text-2xl font-bold text-white leading-relaxed">
                    {currentQ.question || currentQ}
                  </h3>
                  {currentQ.expected_skills && currentQ.expected_skills.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-700/60">
                      <span className="text-xs text-slate-400 flex items-center">
                        Key Competencies:
                      </span>
                      {currentQ.expected_skills.map((sk, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-0.5 bg-slate-900 text-slate-300 rounded-md text-xs border border-slate-700"
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Answer Editor */}
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Your Response
                  </label>
                  <textarea
                    rows="6"
                    placeholder="Provide a detailed answer. Highlight your architectural trade-offs, error handling, or project experience..."
                    value={currentAnswer}
                    disabled={!!latestEvaluation}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    className="w-full bg-slate-900/80 border border-slate-700 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm leading-relaxed disabled:opacity-60"
                  />

                  {status === 'error' && (
                    <div className="mt-3 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2.5 rounded-xl text-sm">
                      {errorMessage}
                    </div>
                  )}

                  {!latestEvaluation ? (
                    <button
                      onClick={handleAnswerSubmit}
                      disabled={!currentAnswer.trim() || status === 'evaluating'}
                      className="mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/40 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all flex items-center gap-2"
                    >
                      {status === 'evaluating' ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Evaluating Response with AI...</span>
                        </>
                      ) : (
                        <>
                          <span>Submit Answer for Evaluation</span>
                          <CheckCircle2 className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  ) : (
                    /* Evaluation Card (Shown immediately after submitting answer) */
                    <div className="mt-6 pt-6 border-t border-slate-700 space-y-5 animate-in fade-in">
                      <div className="flex items-center justify-between">
                        <h4 className="text-lg font-bold text-white flex items-center gap-2">
                          <Award className="w-5 h-5 text-yellow-400" />
                          <span>AI Answer Evaluation</span>
                        </h4>

                        <div className="flex gap-2">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold border ${getScoreColor(
                              latestEvaluation.technical_score
                            )}`}
                          >
                            Tech: {latestEvaluation.technical_score}%
                          </span>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-bold border ${getScoreColor(
                              latestEvaluation.communication_score
                            )}`}
                          >
                            Comm: {latestEvaluation.communication_score}%
                          </span>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-900/60 border border-slate-700/80 rounded-xl text-sm text-slate-200 leading-relaxed">
                        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                          Critique & Feedback
                        </div>
                        {latestEvaluation.feedback}
                      </div>

                      {/* Toggle Ideal Answer */}
                      <div>
                        <button
                          onClick={() => setShowIdealAnswer(!showIdealAnswer)}
                          className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1 underline"
                        >
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>
                            {showIdealAnswer
                              ? 'Hide Exemplary Answer'
                              : 'View Exemplary Answer'}
                          </span>
                        </button>

                        {showIdealAnswer && (
                          <div className="mt-2 p-4 bg-blue-950/30 border border-blue-500/30 rounded-xl text-sm text-blue-200">
                            <div className="text-xs font-bold text-blue-400 mb-1">
                              Exemplary Architectural Answer:
                            </div>
                            {latestEvaluation.ideal_answer}
                          </div>
                        )}
                      </div>

                      {/* Adaptive Follow-up question */}
                      {latestEvaluation.follow_up_questions?.length > 0 && (
                        <div className="p-4 bg-purple-950/30 border border-purple-500/30 rounded-xl text-sm text-purple-200">
                          <div className="text-xs font-bold text-purple-400 mb-1 flex items-center gap-1.5">
                            <HelpCircle className="w-4 h-4" />
                            <span>Adaptive AI Follow-Up Challenge:</span>
                          </div>
                          {latestEvaluation.follow_up_questions[0]}
                        </div>
                      )}

                      <div className="flex justify-end pt-2">
                        <button
                          onClick={handleNextQuestion}
                          disabled={status === 'finishing'}
                          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl shadow-lg transition-all flex items-center gap-2"
                        >
                          {status === 'finishing' ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Generating Executive Report...</span>
                            </>
                          ) : (
                            <>
                              <span>
                                {currentQuestionIndex < session.questions.length - 1
                                  ? 'Next Question'
                                  : 'Finish Interview & View Report'}
                              </span>
                              <ArrowRight className="w-4 h-4" />
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* STEP 3: EXECUTIVE INTERVIEW REPORT CARD */}
            {step === 3 && session && (
              <div className="space-y-8 animate-in fade-in duration-300">
                {/* Hero Overall Gauge Card */}
                <div className="bg-gradient-to-r from-slate-800/90 to-blue-950/40 border border-slate-700 rounded-3xl p-8 text-center relative overflow-hidden shadow-2xl">
                  <div className="inline-flex items-center justify-center w-28 h-28 rounded-full border-4 border-blue-500/40 bg-blue-500/10 mb-4 shadow-inner">
                    <span className="text-4xl font-extrabold text-blue-400">
                      {session.overall_score}%
                    </span>
                  </div>

                  <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-2">
                    {session.role} — Interview Report
                  </h2>

                  <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
                    <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-bold">
                      {session.report?.interview_readiness || 'Proficient'}
                    </span>
                    <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold">
                      Recommendation: {session.report?.hiring_recommendation || 'Hire'}
                    </span>
                    <span className="px-3 py-1 rounded-full bg-slate-700 text-slate-300 text-xs">
                      {session.difficulty} • {session.interview_type}
                    </span>
                  </div>

                  <p className="text-slate-300 max-w-2xl mx-auto text-sm leading-relaxed mb-6">
                    {session.report?.executive_summary ||
                      `Candidate completed ${session.questions.length} personalized questions with overall proficiency ${session.overall_score}%.`}
                  </p>

                  <div className="flex flex-wrap items-center justify-center gap-4">
                    <Link
                      to="/digital-twin"
                      className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-full border border-slate-600/60 transition-all text-sm flex items-center gap-2"
                    >
                      <Award className="w-4 h-4 text-yellow-400" />
                      <span>View Memory Timeline in Digital Twin</span>
                    </Link>
                    <button
                      onClick={() => {
                        setStep(1);
                        setSession(null);
                      }}
                      className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-full shadow-lg transition-all text-sm flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Start Another Mock Interview</span>
                    </button>
                  </div>
                </div>

                {/* Dimension Scores Breakdown Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Technical Depth
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {session.technical_score}%
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full"
                        style={{ width: `${session.technical_score}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Communication Clarity
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {session.communication_score}%
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full"
                        style={{ width: `${session.communication_score}%` }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Problem Solving
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {session.report?.problem_solving_score || session.technical_score}%
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-purple-500 h-full"
                        style={{
                          width: `${
                            session.report?.problem_solving_score ||
                            session.technical_score
                          }%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Confidence
                    </div>
                    <div className="text-2xl font-bold text-white">
                      {session.confidence_score}%
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="bg-yellow-500 h-full"
                        style={{ width: `${session.confidence_score}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Strengths & Weaknesses Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-slate-800/40 border border-emerald-500/20 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-emerald-400 mb-4 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5" />
                      <span>Key Interview Strengths</span>
                    </h3>
                    <ul className="space-y-2.5 text-sm text-slate-300">
                      {session.report?.strengths?.map((str, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-400 font-bold">•</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-slate-800/40 border border-red-500/20 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      <span>Areas for Technical Improvement</span>
                    </h3>
                    <ul className="space-y-2.5 text-sm text-slate-300">
                      {session.report?.weaknesses?.map((wk, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-red-400 font-bold">•</span>
                          <span>{wk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Recommended Projects & Action Items */}
                {session.report?.recommended_projects?.length > 0 && (
                  <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-blue-400" />
                      <span>Recommended Production Practice Projects</span>
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                      {session.report.recommended_projects.map((proj, idx) => (
                        <div
                          key={idx}
                          className="p-4 bg-slate-900/60 border border-slate-700 rounded-xl text-sm text-slate-200"
                        >
                          {proj}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function maxHeightPct(val) {
  const n = Number(val) || 0;
  return Math.min(100, Math.max(15, n));
}
