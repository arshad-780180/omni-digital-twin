import api from './api';

// ==========================================
// Legacy endpoints (Backward Compatibility)
// ==========================================
export const syncGitHubProfile = async (username) => {
  const response = await api.post('/github/sync', { username });
  return response.data;
};

export const getGitHubReport = async () => {
  const response = await api.get('/github/report');
  return response.data;
};

// ==========================================
// Phase 2: AI GitHub Intelligence Engine
// ==========================================
export const analyzeGitHub = async (username) => {
  const response = await api.post('/github/analyze', { username });
  return response.data;
};

export const getGitHubLatest = async () => {
  const response = await api.get('/github/latest');
  return response.data;
};

export const getGitHubProfile = async () => {
  const response = await api.get('/github/profile');
  return response.data;
};

export const getGitHubRepos = async () => {
  const response = await api.get('/github/repos');
  return response.data;
};
