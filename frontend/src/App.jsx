import { useState } from 'react'

function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex justify-between items-center backdrop-blur-sm sticky top-0 z-10">
        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          OmniMind
        </div>
        <nav>
          <ul className="flex space-x-6 text-sm font-medium">
            <li className="hover:text-blue-400 transition-colors cursor-pointer">Dashboard</li>
            <li className="hover:text-blue-400 transition-colors cursor-pointer">Profile</li>
            <li className="hover:text-blue-400 transition-colors cursor-pointer">Interviews</li>
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
          <button className="px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-full font-semibold transition-all transform hover:scale-105 shadow-lg shadow-blue-500/30">
            Get Started
          </button>
        </div>
      </main>

      <footer className="py-6 text-center text-slate-500 text-sm border-t border-slate-800">
        &copy; {new Date().getFullYear()} OmniMind. All rights reserved.
      </footer>
    </div>
  )
}

export default App
