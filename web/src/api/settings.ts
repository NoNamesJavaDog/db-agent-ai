import apiClient from './client';
import type { Settings } from '../types';

export const settingsApi = {
  get: () => apiClient.get<Settings>('/settings'),
  update: (data: Partial<Settings>) => apiClient.put<Settings>('/settings', data),
};
