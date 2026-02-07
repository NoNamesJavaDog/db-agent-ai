import apiClient from './client';
import type { Provider, ProviderCreate, ProviderUpdate, AvailableProvider } from '../types';

export const providersApi = {
  list: () => apiClient.get<Provider[]>('/providers'),
  create: (data: ProviderCreate) => apiClient.post<Provider>('/providers', data),
  update: (id: number, data: ProviderUpdate) => apiClient.put<Provider>(`/providers/${id}`, data),
  delete: (id: number) => apiClient.delete(`/providers/${id}`),
  activate: (id: number) => apiClient.post(`/providers/${id}/activate`),
  available: () => apiClient.get<AvailableProvider[]>('/providers/available'),
};
