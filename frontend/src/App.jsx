import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import GitHubSync from './pages/GitHubSync';
import CareerReadiness from './pages/CareerReadiness';
import MockInterview from './pages/MockInterview';
import ATSOptimizer from './pages/ATSOptimizer';
import JobMatch from './pages/JobMatch';
import DigitalTwin from './pages/DigitalTwin';
import LearningRoadmap from './pages/LearningRoadmap';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import ProtectedRoute from './components/ProtectedRoute';

function Home() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex justify-between items-center backdrop-blur-sm sticky top-0 z-10">
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          OmniMind
        </div>
        <nav>
          <ul className="flex space-x-6 text-sm font-medium items-center">
            <li><Link to="/login" className="hover:text-blue-400 transition-colors">Login</Link></li>
            <li>
              <Link to="/register" className="px-4 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/50 rounded-full hover:bg-blue-600/30 transition-colors">
                Sign Up
              </Link>
            </li>
          </ul>
        </nav>
      </header>
      
      <main className="flex-grow p-8 flex flex-col items-center justify-center">
        <div className="max-w-3xl text-center space-y-6">
          <h1 className="text-5xl font-extrabold tracking-tight">
            Your Personal <span className="text-blue-500">Digital Twin</span>
          </h1>
          <p className="text-xl text-slate-400">
            Aggregate your professional footprint, analyze skills, and get personalized career roadmaps with AI.
          </p>
          <Link to="/register" className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-full font-semibold transition-all transform hover:scale-105 shadow-lg shadow-blue-500/30">
            Get Started
          </Link>
        </div>
      </main>

      <footer className="py-6 text-center text-slate-500 text-sm border-t border-slate-800">
        &copy; {new Date().getFullYear()} OmniMind. All rights reserved.
      </footer>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/github" 
            element={
              <ProtectedRoute>
                <GitHubSync />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/career" 
            element={
              <ProtectedRoute>
                <CareerReadiness />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/interview" 
            element={
              <ProtectedRoute>
                <MockInterview />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/ats" 
            element={
              <ProtectedRoute>
                <ATSOptimizer />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/job-match" 
            element={
              <ProtectedRoute>
                <JobMatch />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/digital-twin" 
            element={
              <ProtectedRoute>
                <DigitalTwin />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/learning" 
            element={
              <ProtectedRoute>
                <LearningRoadmap />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/analytics" 
            element={
              <ProtectedRoute>
                <AnalyticsDashboard />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
