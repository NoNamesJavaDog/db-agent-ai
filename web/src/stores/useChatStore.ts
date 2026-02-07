import { create } from 'zustand';
import type { ChatMessage, PendingOperation, MigrationSetup, MigrationProgress, MessagePart, FormInputRequest } from '../types';

interface ChatStore {
  messages: ChatMessage[];
  isStreaming: boolean;
  addMessage: (msg: ChatMessage) => void;
  appendToLastAssistant: (delta: string) => void;
  addToolCall: (name: string, input: Record<string, any>) => void;
  updateToolResult: (name: string, status: string, summary: string) => void;
  addPendingToLastAssistant: (ops: PendingOperation[]) => void;
  resolvePending: (msgId: string, result: string) => void;
  addMigrationSetupToLastAssistant: (setup: MigrationSetup) => void;
  resolveMigrationSetup: (msgId: string, resultText: string) => void;
  updateMigrationProgress: (progress: MigrationProgress) => void;
  addFormInputToLastAssistant: (formRequest: FormInputRequest) => void;
  resolveFormInput: (msgId: string, summary: string) => void;
  setStreaming: (v: boolean) => void;
  clearMessages: () => void;
  loadFromHistory: (msgs: ChatMessage[]) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  appendToLastAssistant: (delta) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        const parts = [...(last.parts || [])];
        const lastPart = parts[parts.length - 1];
        if (lastPart && lastPart.type === 'text') {
          parts[parts.length - 1] = { ...lastPart, content: lastPart.content + delta };
        } else {
          parts.push({ type: 'text', content: delta });
        }
        msgs[msgs.length - 1] = { ...last, content: last.content + delta, parts };
      }
      return { messages: msgs };
    }),

  addToolCall: (name, input) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        const toolCalls = [...(last.toolCalls || []), { name, input, status: 'running' as const }];
        const parts: MessagePart[] = [...(last.parts || []), { type: 'tool', toolIndex: toolCalls.length - 1 }];
        msgs[msgs.length - 1] = { ...last, toolCalls, parts };
      }
      return { messages: msgs };
    }),

  updateToolResult: (name, status, summary) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant' && last.toolCalls) {
        const toolCalls = last.toolCalls.map((tc) =>
          tc.name === name && tc.status === 'running'
            ? { ...tc, status: status as 'success' | 'error', summary }
            : tc
        );
        msgs[msgs.length - 1] = { ...last, toolCalls };
      }
      return { messages: msgs };
    }),

  addPendingToLastAssistant: (ops) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, pending: ops };
      }
      return { messages: msgs };
    }),

  resolvePending: (msgId, result) =>
    set((s) => {
      const msgs = s.messages.map((m) =>
        m.id === msgId ? { ...m, pending: undefined, content: m.content + (m.content ? '\n\n' : '') + result } : m
      );
      return { messages: msgs };
    }),

  addMigrationSetupToLastAssistant: (setup) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, migrationSetup: setup };
      }
      return { messages: msgs };
    }),

  resolveMigrationSetup: (msgId, resultText) =>
    set((s) => {
      const msgs = s.messages.map((m) =>
        m.id === msgId
          ? { ...m, migrationSetup: undefined, content: m.content + (m.content ? '\n\n' : '') + resultText }
          : m
      );
      return { messages: msgs };
    }),

  updateMigrationProgress: (progress) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, migrationProgress: progress };
      }
      return { messages: msgs };
    }),

  addFormInputToLastAssistant: (formRequest) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, formInput: formRequest };
      }
      return { messages: msgs };
    }),

  resolveFormInput: (msgId, summary) =>
    set((s) => {
      const msgs = s.messages.map((m) =>
        m.id === msgId
          ? { ...m, formInput: undefined, content: m.content + (m.content ? '\n\n' : '') + summary }
          : m
      );
      return { messages: msgs };
    }),

  setStreaming: (v) => set({ isStreaming: v }),

  clearMessages: () => set({ messages: [] }),

  loadFromHistory: (msgs) => set({ messages: msgs }),
}));
