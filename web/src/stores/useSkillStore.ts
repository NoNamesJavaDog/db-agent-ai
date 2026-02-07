import { create } from 'zustand';
import { skillsApi } from '../api/skills';
import type { Skill, SkillDetail } from '../types';

interface SkillStore {
  skills: Skill[];
  loading: boolean;
  fetch: () => Promise<void>;
  reload: () => Promise<void>;
  getDetail: (name: string) => Promise<SkillDetail>;
}

export const useSkillStore = create<SkillStore>((set) => ({
  skills: [],
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const res = await skillsApi.list();
      set({ skills: res.data });
    } finally {
      set({ loading: false });
    }
  },
  reload: async () => {
    await skillsApi.reload();
    const res = await skillsApi.list();
    set({ skills: res.data });
  },
  getDetail: async (name: string) => {
    const res = await skillsApi.detail(name);
    return res.data;
  },
}));
