import api from './api';

export const generateRoadmap = async ({ target_role, target_timeframe_weeks = 8, focus_areas = [] }) => {
  const response = await api.post('/learning/generate', {
    target_role,
    target_timeframe_weeks,
    focus_areas,
  });
  return response.data;
};

export const getLatestRoadmap = async () => {
  const response = await api.get('/learning/latest');
  return response.data;
};

export const getRoadmapHistory = async () => {
  const response = await api.get('/learning/history');
  return response.data;
};

export const getRoadmapById = async (id) => {
  const response = await api.get(`/learning/${id}`);
  return response.data;
};

export const completeMilestone = async (id, { milestone_id, notes = '', completed_items = [] } = {}) => {
  const targetMilestone = milestone_id || id;
  const response = await api.post(`/learning/milestone/${targetMilestone}/complete`, {
    milestone_id: targetMilestone,
    notes,
    completed_items,
  });
  return response.data;
};

export const completeMilestoneOnRoadmap = async (roadmapId, milestoneId, { notes = '', completed_items = [] } = {}) => {
  const response = await api.post(`/learning/${roadmapId}/milestone/${milestoneId}/complete`, {
    milestone_id: milestoneId,
    notes,
    completed_items,
  });
  return response.data;
};

export const recalculateRoadmap = async () => {
  const response = await api.post('/learning/recalculate');
  return response.data;
};

export const deleteRoadmap = async (id) => {
  const response = await api.delete(`/learning/${id}`);
  return response.data;
};
