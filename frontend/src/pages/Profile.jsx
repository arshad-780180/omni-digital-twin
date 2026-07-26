import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getProfile } from '../services/profile';
import ResumeUpload from '../components/ResumeUpload';
import { User, Mail, Briefcase, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
    } catch (error) {
      console.error("Failed to load profile", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUploadSuccess = (extractedSkills) => {
    // Re-fetch profile to get updated skills
    fetchProfile();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-400 mt-4 font-medium">Loading Digital Twin...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      <header className="px-6 py-4 border-b border-slate-800 flex items-center gap-4 sticky top-0 z-10 bg-slate-900/80 backdrop-blur-md">
        <Link to="/dashboard" className="p-2 hover:bg-slate-800 rounded-full transition-colors">
          <ChevronLeft className="w-5 h-5 text-slate-400" />
        </Link>
        <div className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          Digital Twin Profile
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 md:p-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Basic Info & Resume Upload */}
          <div className="lg:col-span-1 space-y-8">
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-full flex items-center justify-center text-2xl font-bold shadow-lg shadow-blue-500/20">
                  {user?.email?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2 className="text-xl font-bold">{profile?.full_name || 'Anonymous User'}</h2>
                  <p className="text-slate-400 text-sm flex items-center gap-1 mt-1">
                    <Mail className="w-3 h-3" />
                    {user?.email}
                  </p>
                </div>
              </div>
            </div>

            <ResumeUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Right Column: Skills Graph & Details */}
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm min-h-[400px]">
              <div className="flex items-center gap-3 mb-6 border-b border-slate-700 pb-4">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                  <Briefcase className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold">Extracted Skill Set</h3>
              </div>
              
              {profile?.skills && profile.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill, index) => (
                    <span 
                      key={index} 
                      className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-full text-sm font-medium text-slate-300 shadow-sm hover:border-blue-500/50 hover:text-blue-400 transition-colors cursor-default"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="h-48 flex flex-col items-center justify-center text-slate-500">
                  <Briefcase className="w-12 h-12 mb-3 opacity-20" />
                  <p>No skills extracted yet.</p>
                  <p className="text-sm">Upload your resume to build your skill graph.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
