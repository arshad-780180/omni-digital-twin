import api from './api';

export const generateInterview = async (targetRole) => {
  const response = await api.post('/interview/generate', { target_role: targetRole });
  return response.data;
};

export const evaluateInterview = async (interviewId, answers) => {
  const response = await api.post(`/interview/evaluate/${interviewId}`, { answers });
  return response.data;
};
