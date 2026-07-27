import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex justify-between items-center backdrop-blur-sm sticky top-0 z-10 bg-slate-900/80">
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          OmniMind
        </div>
        <nav className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-slate-300 bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
            <UserIcon className="w-4 h-4" />
            <span className="text-sm font-medium">{user?.email}</span>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </nav>
      </header>

      <main className="flex-grow p-8 max-w-7xl mx-auto w-full">
        <div className="mb-8">
          <h1 className="text-4xl font-bold">Dashboard</h1>
          <p className="text-slate-400 mt-2">Welcome to your Digital Twin command center.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Placeholder Cards for Future Phases */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">Resume Intelligence</h3>
            <p className="text-sm text-slate-400 mb-4">Upload your resume to extract skills and experience.</p>
            <Link to="/profile" className="inline-block text-blue-400 text-sm font-medium hover:text-blue-300">Go to Profile &rarr;</Link>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">GitHub Sync</h3>
            <p className="text-sm text-slate-400 mb-4">Connect your GitHub to analyze your coding style.</p>
            <Link to="/github" className="inline-block text-blue-400 text-sm font-medium hover:text-blue-300">Connect &rarr;</Link>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">Career Readiness</h3>
            <p className="text-sm text-slate-400 mb-4">Compare your digital twin against job descriptions.</p>
            <Link to="/career" className="inline-block text-blue-400 text-sm font-medium hover:text-blue-300">Analyze &rarr;</Link>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">Mock Interview</h3>
            <p className="text-sm text-slate-400 mb-4">Practice AI-generated technical interview questions.</p>
            <Link to="/interview" className="inline-block text-blue-400 text-sm font-medium hover:text-blue-300">Start Interview &rarr;</Link>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">ATS Optimizer</h3>
            <p className="text-sm text-slate-400 mb-4">Optimize your resume against target job descriptions.</p>
            <Link to="/ats" className="inline-block text-emerald-400 text-sm font-medium hover:text-emerald-300">Optimize Resume &rarr;</Link>
          </div>

          <div className="bg-slate-800/50 border border-emerald-500/40 rounded-xl p-6 backdrop-blur-sm shadow-lg shadow-emerald-500/10">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              AI Job Matching Engine
            </h3>
            <p className="text-sm text-slate-400 mb-4">Evaluate your Digital Twin fit, get role recommendations, salary ranges & learning plans.</p>
            <Link to="/job-match" className="inline-block text-emerald-400 text-sm font-medium hover:text-emerald-300">Evaluate Match &rarr;</Link>
          </div>

          <div className="bg-gradient-to-br from-indigo-900/40 via-slate-800/80 to-blue-900/40 border border-indigo-500/40 rounded-xl p-6 backdrop-blur-sm shadow-xl shadow-indigo-500/10 col-span-1 md:col-span-2">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-white">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-pulse"></span>
              AI Digital Twin Memory Engine
            </h3>
            <p className="text-sm text-slate-300 mb-4">View your persistent, living AI representation. Explore your career synthesis, mastered skills, evolution timeline, and historical insights.</p>
            <Link to="/digital-twin" className="inline-block text-indigo-300 text-sm font-medium hover:text-indigo-200">Open Digital Twin &rarr;</Link>
          </div>

          <div className="bg-gradient-to-br from-violet-900/40 via-slate-800/80 to-indigo-900/40 border border-violet-500/40 rounded-xl p-6 backdrop-blur-sm shadow-xl shadow-violet-500/10 col-span-1 md:col-span-2">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-white">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse"></span>
              AI Personalized Learning Roadmap Engine
            </h3>
            <p className="text-sm text-slate-300 mb-4">Your continuous AI Career Mentor. Generate multi-phase learning plans, track milestone completion, and evolve your Digital Twin Memory automatically.</p>
            <Link to="/learning" className="inline-block text-violet-300 text-sm font-medium hover:text-violet-200">Open AI Career Mentor &rarr;</Link>
          </div>

          <div className="bg-gradient-to-br from-blue-900/50 via-slate-800/90 to-emerald-900/50 border border-blue-500/50 rounded-xl p-6 backdrop-blur-sm shadow-2xl shadow-blue-500/15 col-span-1 md:col-span-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-bold flex items-center gap-2 text-white">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse"></span>
                Executive Analytics & Career Intelligence Dashboard (v1.0)
              </h3>
              <span className="text-xs font-semibold bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full border border-blue-500/30">
                v1.0 Production
              </span>
            </div>
            <p className="text-sm text-slate-300 mb-4">
              Your executive command center. Unified Career Health Score, 11-skill growth matrix, chronological career timeline, AI executive insights, and downloadable ReportLab PDF reports.
            </p>
            <Link to="/analytics" className="inline-block px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-all shadow-md shadow-blue-600/30">
              Open Executive Dashboard &rarr;
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
