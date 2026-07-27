import api from './api';

export const analyzeATS = async (jobTitle, company, jobDescription) => {
  const response = await api.post('/ats/analyze', {
    job_title: jobTitle,
    company: company,
    job_description: jobDescription
  });
  return response.data;
};

export const getATSLatest = async () => {
  const response = await api.get('/ats/latest');
  return response.data;
};

export const getATSHistory = async () => {
  const response = await api.get('/ats/history');
  return response.data;
};

export const deleteATSAnalysis = async (analysisId) => {
  const response = await api.delete(`/ats/${analysisId}`);
  return response.data;
};
