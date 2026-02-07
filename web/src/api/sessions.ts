import apiClient from './client';
import type { Session, SessionCreate, Message } from '../types';

export const sessionsApi = {
  list: () => apiClient.get<Session[]>('/sessions'),
  create: (data: SessionCreate) => apiClient.post<Session>('/sessions', data),
  delete: (id: number) => apiClient.delete(`/sessions/${id}`),
  rename: (id: number, name: string) => apiClient.put(`/sessions/${id}/rename`, { name }),
  activate: (id: number) => apiClient.post(`/sessions/${id}/activate`),
  messages: (id: number) => apiClient.get<Message[]>(`/sessions/${id}/messages`),
  reset: (id: number) => apiClient.post(`/sessions/${id}/reset`),
};
