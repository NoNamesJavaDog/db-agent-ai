import apiClient from './client';
import type { McpServer, McpServerCreate, McpTool } from '../types';

export const mcpApi = {
  listServers: () => apiClient.get<McpServer[]>('/mcp/servers'),
  addServer: (data: McpServerCreate) => apiClient.post<McpServer>('/mcp/servers', data),
  deleteServer: (name: string) => apiClient.delete(`/mcp/servers/${name}`),
  enableServer: (name: string) => apiClient.post(`/mcp/servers/${name}/enable`),
  disableServer: (name: string) => apiClient.post(`/mcp/servers/${name}/disable`),
  connectServer: (name: string) => apiClient.post(`/mcp/servers/${name}/connect`),
  getServerTools: (name: string) => apiClient.get<McpTool[]>(`/mcp/servers/${name}/tools`),
  getAllTools: () => apiClient.get<McpTool[]>('/mcp/tools'),
  getStatus: () => apiClient.get('/mcp/status'),
  healthCheck: () => apiClient.get('/mcp/health'),
};
