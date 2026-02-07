import apiClient from './client';
import type { PendingOperation } from '../types';

export const chatApi = {
  interrupt: (sessionId: number) => apiClient.post(`/chat/${sessionId}/interrupt`),
  getPending: (sessionId: number) =>
    apiClient.get<{ has_pending: boolean; pending_count: number; operations: PendingOperation[] }>(
      `/chat/${sessionId}/pending`
    ),
  confirm: (sessionId: number, index: number) =>
    apiClient.post(`/chat/${sessionId}/confirm`, { index }),
  confirmAll: (sessionId: number) => apiClient.post(`/chat/${sessionId}/confirm-all`),
  skipAll: (sessionId: number) => apiClient.post(`/chat/${sessionId}/skip-all`),
  upload: (sessionId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/chat/${sessionId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  startMigration: (sessionId: number, data: {
    source_connection_id: number;
    target_connection_id: number;
    source_schema?: string;
    target_schema?: string;
    auto_execute?: boolean;
  }) => apiClient.post<{ success: boolean; task_id: number; instruction: string }>(
    `/chat/${sessionId}/start-migration`,
    data
  ),
  submitForm: (sessionId: number, values: Record<string, any>) =>
    apiClient.post<{ success: boolean; instruction: string }>(
      `/chat/${sessionId}/submit-form`,
      { values }
    ),
};
