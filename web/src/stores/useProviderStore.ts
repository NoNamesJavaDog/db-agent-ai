import { create } from 'zustand';
import { providersApi } from '../api/providers';
import type { Provider, ProviderCreate, ProviderUpdate, AvailableProvider } from '../types';

interface ProviderStore {
  providers: Provider[];
  available: AvailableProvider[];
  loading: boolean;
  fetch: () => Promise<void>;
  fetchAvailable: () => Promise<void>;
  create: (data: ProviderCreate) => Promise<Provider>;
  update: (id: number, data: ProviderUpdate) => Promise<void>;
  remove: (id: number) => Promise<void>;
  activate: (id: number) => Promise<void>;
}

export const useProviderStore = create<ProviderStore>((set, get) => ({
  providers: [],
  available: [],
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const res = await providersApi.list();
      set({ providers: res.data });
    } finally {
      set({ loading: false });
    }
  },
  fetchAvailable: async () => {
    const res = await providersApi.available();
    set({ available: res.data });
  },
  create: async (data) => {
    const res = await providersApi.create(data);
    await get().fetch();
    return res.data;
  },
  update: async (id, data) => {
    await providersApi.update(id, data);
    await get().fetch();
  },
  remove: async (id) => {
    await providersApi.delete(id);
    await get().fetch();
  },
  activate: async (id) => {
    await providersApi.activate(id);
    await get().fetch();
  },
}));
