import { useCallback, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useChatStore } from '../stores/useChatStore';
import type { PendingOperation, FormInputRequest } from '../types';

export function useSSEChat(sessionId: number | null) {
  const abortRef = useRef<AbortController | null>(null);
  const {
    addMessage,
    addToolCall,
    updateToolResult,
    appendToLastAssistant,
    addPendingToLastAssistant,
    addMigrationSetupToLastAssistant,
    updateMigrationProgress,
    addFormInputToLastAssistant,
    setStreaming,
  } = useChatStore();

  const sendMessage = useCallback(
    async (message: string, isAutoRetry = false) => {
      if (!sessionId) return;

      if (!isAutoRetry) {
        // Add user message (skip for auto-retry since it's already in history)
        addMessage({
          id: `user-${Date.now()}`,
          role: 'user',
          content: message,
        });
      }

      // Add empty assistant message
      addMessage({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        isStreaming: true,
      });

      setStreaming(true);
      const pendingOps: PendingOperation[] = [];
      let formInputData: FormInputRequest | null = null;

      abortRef.current = new AbortController();

      try {
        await fetchEventSource(`/api/v2/chat/${sessionId}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
          signal: abortRef.current.signal,
          onmessage(ev) {
            if (!ev.event || !ev.data) return;
            try {
              const data = JSON.parse(ev.data);
              switch (ev.event) {
                case 'tool_call':
                  addToolCall(data.name, data.input || {});
                  break;
                case 'tool_result':
                  updateToolResult(data.name, data.status || 'success', data.summary || '');
                  break;
                case 'text_delta':
                  appendToLastAssistant(data.content || '');
                  break;
                case 'pending':
                  pendingOps.push(data);
                  break;
                case 'migration_setup':
                  addMigrationSetupToLastAssistant(data);
                  break;
                case 'migration_progress':
                  updateMigrationProgress(data);
                  break;
                case 'form_input':
                  formInputData = data;
                  break;
                case 'done':
                  if (data.has_pending && pendingOps.length > 0) {
                    addPendingToLastAssistant(pendingOps);
                  }
                  if (formInputData) {
                    addFormInputToLastAssistant(formInputData);
                  }
                  break;
                case 'error':
                  appendToLastAssistant(`Error: ${data.message}`);
                  break;
              }
            } catch {
              // ignore parse errors
            }
          },
          onerror(err) {
            console.error('SSE error:', err);
            throw err; // stop retrying
          },
          onclose() {
            setStreaming(false);
          },
        });
      } catch {
        // aborted or error
      } finally {
        setStreaming(false);
        abortRef.current = null;
      }
    },
    [sessionId, addMessage, addToolCall, updateToolResult, appendToLastAssistant, addPendingToLastAssistant, addMigrationSetupToLastAssistant, updateMigrationProgress, addFormInputToLastAssistant, setStreaming]
  );

  const interrupt = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { sendMessage, interrupt };
}
