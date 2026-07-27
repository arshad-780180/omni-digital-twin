import api from './api';

export const getDashboardSummary = async () => {
  const response = await api.get('/analytics/dashboard');
  return response.data;
};

export const getCareerAnalytics = async () => {
  const response = await api.get('/analytics/career');
  return response.data;
};

export const getATSAnalytics = async () => {
  const response = await api.get('/analytics/ats');
  return response.data;
};

export const getJobMatchAnalytics = async () => {
  const response = await api.get('/analytics/job-match');
  return response.data;
};

export const getInterviewAnalytics = async () => {
  const response = await api.get('/analytics/interviews');
  return response.data;
};

export const getLearningAnalytics = async () => {
  const response = await api.get('/analytics/learning');
  return response.data;
};

export const getSkillMatrix = async () => {
  const response = await api.get('/analytics/skills');
  return response.data;
};

export const getTimeline = async () => {
  const response = await api.get('/analytics/timeline');
  return response.data;
};

export const downloadReport = async (reportType = 'career') => {
  const response = await api.get('/analytics/export', {
    params: { report_type: reportType },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `omni_${reportType}_report.pdf`);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};
