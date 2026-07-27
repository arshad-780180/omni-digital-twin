import api from './api';

export const getDigitalTwinMemory = async () => {
  const response = await api.get('/twin');
  return response.data;
};

export const getDigitalTwinSummary = async () => {
  const response = await api.get('/twin/summary');
  return response.data;
};

export const getDigitalTwinTimeline = async () => {
  const response = await api.get('/twin/timeline');
  return response.data;
};

export const rebuildDigitalTwinMemory = async () => {
  const response = await api.post('/twin/rebuild');
  return response.data;
};
