import api from './api';

export const getProfile = async () => {
  const response = await api.get('/profile');
  return response.data;
};

export const uploadResume = async (formData) => {
  const response = await api.post('/profile/resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const updateSkills = async (skills) => {
  const response = await api.post('/profile/skills', skills);
  return response.data;
};
