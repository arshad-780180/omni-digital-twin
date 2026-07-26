import { useState } from 'react';
import { generateInterview, evaluateInterview } from '../services/interview';
import { Bot, Loader2, ChevronLeft, ArrowRight, CheckCircle2, MessageSquare, Target } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function MockInterview() {
  const [step, setStep] = useState(1); // 1: Setup, 2: Q&A, 3: Results
  const [targetRole, setTargetRole] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating, evaluating, error
  const [errorMessage, setErrorMessage] = useState('');
  
  const [session, setSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [answers, setAnswers] = useState([]);

  const handleStart = async (e) => {
    e.preventDefault();
    if (!targetRole.trim()) return;

    setStatus('generating');
    setErrorMessage('');
    
    try {
      const data = await generateInterview(targetRole.trim());
      setSession(data);
      setStep(2);
      setStatus('idle');
      setCurrentQuestionIndex(0);
      setAnswers(new Array(data.questions.length).fill(''));
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to generate interview.');
    }
  };

  const handleNextQuestion = () => {
    const updatedAnswers = [...answers];
    updatedAnswers[currentQuestionIndex] = currentAnswer;
    setAnswers(updatedAnswers);

    if (currentQuestionIndex < session.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setCurrentAnswer(updatedAnswers[currentQuestionIndex + 1] || '');
    } else {
      handleFinish(updatedAnswers);
    }
  };

  const handleFinish = async (finalAnswers) => {
    setStatus('evaluating');
    setErrorMessage('');
    
    try {
      const data = await evaluateInterview(session.id, finalAnswers);
      setSession(data);
      setStep(3);
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Failed to evaluate interview.');
    }
  };

  const getScoreColor = (score, max) => {
    const pct = (score / max) * 100;
    if (pct >= 80) return 'text-emerald-400 stroke-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (pct >= 50) return 'text-yellow-400 stroke-yellow-400 border-yellow-500/30 bg-yellow-500/10';
    return 'text-red-400 stroke-red-400 border-red-500/30 bg-red-500/10';
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans pb-12">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center gap-4 sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md">
        <Link to="/dashboard" className="p-2 hover:bg-slate-800 rounded-full transition-colors">
          <ChevronLeft className="w-5 h-5 text-slate-400" />
        </Link>
        <div className="text-xl font-bold flex items-center gap-2">
          <Bot className="w-6 h-6 text-blue-400" />
          <span>AI Interview Engine</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6 md:p-8 mt-4">
        
        {step === 1 && (
          <div className="max-w-md mx-auto mt-12 bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur-sm text-center shadow-2xl animate-in fade-in slide-in-from-bottom-4">
            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 transform rotate-3">
              <MessageSquare className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Mock Interview Setup</h2>
            <p className="text-slate-400 mb-8 text-sm">
              Enter your target role, and our AI will generate tailored interview questions to test your readiness.
            </p>

            {status === 'error' && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-6 text-sm">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleStart} className="space-y-4">
              <input 
                type="text" 
                placeholder="e.g. Senior Frontend Engineer"
                className="w-full bg-slate-900/50 border border-slate-700 text-slate-100 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-center"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                required
              />
              <button 
                type="submit"
                disabled={status === 'generating'}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-semibold py-3 rounded-xl flex justify-center items-center gap-2 transition-all shadow-lg shadow-blue-500/20"
              >
                {status === 'generating' ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Generating Questions...</>
                ) : 'Start Interview'}
              </button>
            </form>
          </div>
        )}

        {step === 2 && session && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 md:p-10 backdrop-blur-sm animate-in fade-in zoom-in-95 duration-300">
            <div className="flex justify-between items-center mb-8 pb-6 border-b border-slate-700">
              <div>
                <span className="text-blue-400 font-bold tracking-wider text-sm uppercase">Question {currentQuestionIndex + 1} of {session.questions.length}</span>
                <h2 className="text-2xl font-bold mt-1 text-slate-100 leading-snug">
                  {session.questions[currentQuestionIndex]}
                </h2>
              </div>
            </div>
            
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-400">Your Answer</label>
              <textarea 
                className="w-full h-64 bg-slate-900/50 border border-slate-700 text-slate-100 rounded-xl p-4 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none text-lg leading-relaxed"
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder="Type your answer here as if you were speaking to the interviewer..."
                autoFocus
              />
            </div>

            {status === 'error' && (
              <div className="text-red-400 text-sm mt-4">{errorMessage}</div>
            )}

            <div className="mt-8 flex justify-end">
              <button
                onClick={handleNextQuestion}
                disabled={!currentAnswer.trim() || status === 'evaluating'}
                className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20"
              >
                {status === 'evaluating' ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Evaluating Responses...</>
                ) : currentQuestionIndex < session.questions.length - 1 ? (
                  <>Next Question <ArrowRight className="w-5 h-5" /></>
                ) : (
                  <>Finish Interview <CheckCircle2 className="w-5 h-5" /></>
                )}
              </button>
            </div>
          </div>
        )}

        {step === 3 && session && (
          <div className="animate-in fade-in slide-in-from-bottom-8 duration-500">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold mb-4">Interview Results</h1>
              <p className="text-slate-400">Target Role: <span className="font-semibold text-slate-200">{session.target_role}</span></p>
              
              <div className="mt-8 relative w-48 h-48 flex items-center justify-center mx-auto">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="transparent" strokeWidth="8" className="stroke-slate-700" />
                  <circle 
                    cx="50" cy="50" r="45" fill="transparent" strokeWidth="8" 
                    strokeDasharray="283"
                    strokeDashoffset={283 - (283 * session.overall_score) / 100}
                    strokeLinecap="round"
                    className={`transition-all duration-1000 ease-out ${getScoreColor(session.overall_score, 100).split(' ')[0]}`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-5xl font-bold ${getScoreColor(session.overall_score, 100).split(' ')[0]}`}>
                    {session.overall_score}
                  </span>
                  <span className="text-slate-400 text-sm">Overall Score</span>
                </div>
              </div>
            </div>

            <div className="space-y-8">
              <h3 className="text-2xl font-bold">Detailed Feedback</h3>
              
              {session.feedback?.map((fb, idx) => (
                <div key={idx} className={`border rounded-2xl p-6 ${getScoreColor(fb.score, 10)}`}>
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-lg font-semibold text-slate-100 max-w-2xl">
                      Q: {session.questions[fb.question_index]}
                    </h4>
                    <div className="flex flex-col items-end shrink-0">
                      <span className="text-2xl font-bold">{fb.score}<span className="text-sm opacity-50">/10</span></span>
                    </div>
                  </div>
                  
                  <div className="bg-slate-900/40 rounded-xl p-4 mb-4">
                    <p className="text-sm text-slate-400 uppercase tracking-wider font-bold mb-1">Your Answer</p>
                    <p className="text-slate-200 italic">"{session.answers[fb.question_index]}"</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-slate-400 uppercase tracking-wider font-bold mb-1">AI Critique</p>
                    <p className="text-slate-100 leading-relaxed">{fb.critique}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-12 text-center">
              <button 
                onClick={() => {
                  setStep(1);
                  setSession(null);
                  setTargetRole('');
                }}
                className="bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3 px-8 rounded-xl transition-all"
              >
                Start New Interview
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
