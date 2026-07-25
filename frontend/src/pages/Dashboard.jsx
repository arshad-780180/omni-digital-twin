import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Placeholder Cards for Future Phases */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">Resume Intelligence</h3>
            <p className="text-sm text-slate-400 mb-4">Upload your resume to extract skills and experience.</p>
            <button className="text-blue-400 text-sm font-medium hover:text-blue-300">Go to Profile &rarr;</button>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">GitHub Sync</h3>
            <p className="text-sm text-slate-400 mb-4">Connect your GitHub to analyze your coding style.</p>
            <button className="text-blue-400 text-sm font-medium hover:text-blue-300">Connect &rarr;</button>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-2">Career Readiness</h3>
            <p className="text-sm text-slate-400 mb-4">Compare your digital twin against job descriptions.</p>
            <button className="text-blue-400 text-sm font-medium hover:text-blue-300">Analyze &rarr;</button>
          </div>
        </div>
      </main>
    </div>
  );
}
