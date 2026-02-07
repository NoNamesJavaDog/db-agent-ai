import { create } from 'zustand';
import { mcpApi } from '../api/mcp';
import type { McpServer, McpServerCreate, McpTool } from '../types';

interface McpStore {
  servers: McpServer[];
  tools: McpTool[];
  loading: boolean;
  fetchServers: () => Promise<void>;
  fetchTools: () => Promise<void>;
  addServer: (data: McpServerCreate) => Promise<void>;
  deleteServer: (name: string) => Promise<void>;
  enableServer: (name: string) => Promise<void>;
  disableServer: (name: string) => Promise<void>;
  connectServer: (name: string) => Promise<void>;
}

export const useMcpStore = create<McpStore>((set, get) => ({
  servers: [],
  tools: [],
  loading: false,
  fetchServers: async () => {
    set({ loading: true });
    try {
      const res = await mcpApi.listServers();
      set({ servers: res.data });
    } finally {
      set({ loading: false });
    }
  },
  fetchTools: async () => {
    const res = await mcpApi.getAllTools();
    set({ tools: res.data });
  },
  addServer: async (data) => {
    await mcpApi.addServer(data);
    await get().fetchServers();
  },
  deleteServer: async (name) => {
    await mcpApi.deleteServer(name);
    await get().fetchServers();
  },
  enableServer: async (name) => {
    await mcpApi.enableServer(name);
    await get().fetchServers();
  },
  disableServer: async (name) => {
    await mcpApi.disableServer(name);
    await get().fetchServers();
  },
  connectServer: async (name) => {
    await mcpApi.connectServer(name);
    await get().fetchServers();
    await get().fetchTools();
  },
}));
