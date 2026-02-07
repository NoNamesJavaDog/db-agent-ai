import apiClient from './client';
import type { Skill, SkillDetail } from '../types';

export const skillsApi = {
  list: () => apiClient.get<Skill[]>('/skills'),
  reload: () => apiClient.post('/skills/reload'),
  detail: (name: string) => apiClient.get<SkillDetail>(`/skills/${name}`),
  execute: (name: string, parameters?: Record<string, any>) =>
    apiClient.post(`/skills/${name}/execute`, { parameters }),
};
