import api from './api';

// ==========================================
// Legacy ATS Job-Match Helpers
// ==========================================
export const analyzeJob = async (jobTitle, jobDescription) => {
  const response = await api.post('/career/analyze', { 
    job_title: jobTitle, 
    job_description: jobDescription 
  });
  return response.data;
};

export const getCareerReports = async () => {
  const response = await api.get('/career/reports');
  return response.data;
};

// ==========================================
// Phase 3: AI Career Readiness Helpers
// ==========================================
export const analyzeCareerReadiness = async () => {
  const response = await api.post('/career/analyze', {});
  return response.data;
};

export const getCareerLatest = async () => {
  const response = await api.get('/career/latest');
  return response.data;
};

export const getCareerHistory = async () => {
  const response = await api.get('/career/history');
  return response.data;
};
