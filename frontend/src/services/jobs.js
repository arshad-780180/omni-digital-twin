import api from './api';

export const analyzeJobMatch = async (data) => {
  const response = await api.post('/jobs/analyze', {
    job_title: data.job_title,
    company: data.company || "",
    location: data.location || "",
    employment_type: data.employment_type || "",
    job_description: data.job_description,
  });
  return response.data;
};

export const getJobMatchLatest = async () => {
  const response = await api.get('/jobs/latest');
  return response.data;
};

export const getJobMatchHistory = async () => {
  const response = await api.get('/jobs/history');
  return response.data;
};

export const deleteJobMatch = async (matchId) => {
  const response = await api.delete(`/jobs/${matchId}`);
  return response.data;
};
