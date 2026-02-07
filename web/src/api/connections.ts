import apiClient from './client';
import type { Connection, ConnectionCreate, ConnectionUpdate, ConnectionTestResult, DatabaseListResponse } from '../types';

export const connectionsApi = {
  list: () => apiClient.get<Connection[]>('/connections'),
  create: (data: ConnectionCreate) => apiClient.post<Connection>('/connections', data),
  update: (id: number, data: ConnectionUpdate) => apiClient.put<Connection>(`/connections/${id}`, data),
  delete: (id: number) => apiClient.delete(`/connections/${id}`),
  activate: (id: number) => apiClient.post(`/connections/${id}/activate`),
  test: (id: number) => apiClient.post<ConnectionTestResult>(`/connections/${id}/test`),
  listDatabases: (id: number) => apiClient.get<DatabaseListResponse>(`/connections/${id}/databases`),
  switchDatabase: (id: number, database: string) => apiClient.post<Connection>(`/connections/${id}/switch-db`, { database }),
};
