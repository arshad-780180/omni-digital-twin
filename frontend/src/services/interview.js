import api from './api';

export const startInterview = async ({ role, company = '', difficulty = 'Medium', interview_type = 'Technical', question_count = 5 }) => {
  const response = await api.post('/interview/start', { role, company, difficulty, interview_type, question_count });
  return response.data;
};

export const getInterviewSession = async (sessionId) => {
  const response = await api.get(`/interview/${sessionId}`);
  return response.data;
};

export const submitInterviewAnswer = async (sessionId, { question_id, content, content_type = 'Text' }) => {
  const response = await api.post(`/interview/${sessionId}/answer`, { question_id, content, content_type });
  return response.data;
};

export const finishInterview = async (sessionId) => {
  const response = await api.post(`/interview/${sessionId}/finish`);
  return response.data;
};

export const getLatestInterview = async () => {
  const response = await api.get('/interview/latest');
  return response.data;
};

export const getInterviewHistory = async () => {
  const response = await api.get('/interview/history');
  return response.data;
};

export const deleteInterview = async (sessionId) => {
  const response = await api.delete(`/interview/${sessionId}`);
  return response.data;
};

// Legacy backward-compatible functions
export const generateInterview = async (targetRole) => {
  const response = await api.post('/interview/generate', { target_role: targetRole });
  return response.data;
};

export const evaluateInterview = async (interviewId, answers) => {
  const response = await api.post(`/interview/evaluate/${interviewId}`, { answers });
  return response.data;
};
