import { create } from 'zustand';
import { sessionsApi } from '../api/sessions';
import type { Session, SessionCreate, Message } from '../types';

interface SessionStore {
  sessions: Session[];
  currentSessionId: number | null;
  messages: Message[];
  loading: boolean;
  fetch: () => Promise<void>;
  create: (data: SessionCreate) => Promise<Session>;
  remove: (id: number) => Promise<void>;
  rename: (id: number, name: string) => Promise<void>;
  activate: (id: number) => Promise<void>;
  loadMessages: (id: number) => Promise<void>;
  reset: (id: number) => Promise<void>;
  setCurrentSession: (id: number | null) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const res = await sessionsApi.list();
      set({ sessions: res.data });
    } finally {
      set({ loading: false });
    }
  },
  create: async (data) => {
    const res = await sessionsApi.create(data);
    await get().fetch();
    return res.data;
  },
  remove: async (id) => {
    await sessionsApi.delete(id);
    const state = get();
    if (state.currentSessionId === id) {
      set({ currentSessionId: null, messages: [] });
    }
    await get().fetch();
  },
  rename: async (id, name) => {
    await sessionsApi.rename(id, name);
    await get().fetch();
  },
  activate: async (id) => {
    await sessionsApi.activate(id);
    set({ currentSessionId: id, messages: [] });
    await get().fetch();
    await get().loadMessages(id);
  },
  loadMessages: async (id) => {
    const res = await sessionsApi.messages(id);
    set({ messages: res.data });
  },
  reset: async (id) => {
    await sessionsApi.reset(id);
    if (get().currentSessionId === id) {
      set({ messages: [] });
    }
  },
  setCurrentSession: (id) => set({ currentSessionId: id }),
}));
