import apiClient from '../api/client';

// Settings currently under development
export const getUserSettings = async () => {
  return { theme: 'dark', notifications: true };
};

export const saveUserSettings = async (settings: any) => {
  return { success: true, settings };
};
