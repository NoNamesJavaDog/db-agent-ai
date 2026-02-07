import { create } from 'zustand';
import { connectionsApi } from '../api/connections';
import type { Connection, ConnectionCreate, ConnectionUpdate, ConnectionTestResult, DatabaseListResponse } from '../types';

interface ConnectionStore {
  connections: Connection[];
  loading: boolean;
  fetch: () => Promise<void>;
  create: (data: ConnectionCreate) => Promise<Connection>;
  update: (id: number, data: ConnectionUpdate) => Promise<void>;
  remove: (id: number) => Promise<void>;
  activate: (id: number) => Promise<void>;
  test: (id: number) => Promise<ConnectionTestResult>;
  listDatabases: (id: number) => Promise<DatabaseListResponse>;
  switchDatabase: (id: number, database: string) => Promise<Connection>;
}

export const useConnectionStore = create<ConnectionStore>((set, get) => ({
  connections: [],
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const res = await connectionsApi.list();
      set({ connections: res.data });
    } finally {
      set({ loading: false });
    }
  },
  create: async (data) => {
    const res = await connectionsApi.create(data);
    await get().fetch();
    return res.data;
  },
  update: async (id, data) => {
    await connectionsApi.update(id, data);
    await get().fetch();
  },
  remove: async (id) => {
    await connectionsApi.delete(id);
    await get().fetch();
  },
  activate: async (id) => {
    await connectionsApi.activate(id);
    await get().fetch();
  },
  test: async (id) => {
    const res = await connectionsApi.test(id);
    return res.data;
  },
  listDatabases: async (id) => {
    const res = await connectionsApi.listDatabases(id);
    return res.data;
  },
  switchDatabase: async (id, database) => {
    const res = await connectionsApi.switchDatabase(id, database);
    await get().fetch();
    return res.data;
  },
}));
