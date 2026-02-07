import { useEffect, useRef, useState } from 'react';
import { Input, Button, Space, Empty, Spin } from 'antd';
import { SendOutlined, StopOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import MessageBubble from './MessageBubble';
import FileUploader from './FileUploader';
import { useChatStore } from '../../stores/useChatStore';
import { useSSEChat } from '../../hooks/useSSEChat';
import { useSessionStore } from '../../stores/useSessionStore';
import { chatApi } from '../../api/chat';
import type { ChatMessage } from '../../types';

export default function ChatPanel() {
  const { t } = useTranslation();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionId = useSessionStore((s) => s.currentSessionId);
  const storedMessages = useSessionStore((s) => s.messages);
  const { messages, isStreaming, clearMessages, loadFromHistory } = useChatStore();
  const { sendMessage, interrupt } = useSSEChat(sessionId);

  // Load history when session changes
  useEffect(() => {
    clearMessages();
    if (sessionId) {
      useSessionStore.getState().loadMessages(sessionId);
    }
  }, [sessionId, clearMessages]);

  // Convert stored messages to ChatMessage format (with toolCalls restored)
  useEffect(() => {
    // Only load if messages belong to current session and chat is empty
    if (
      storedMessages.length > 0 &&
      messages.length === 0 &&
      sessionId &&
      storedMessages[0]?.session_id === sessionId
    ) {
      // Build a map: tool_call_id → tool result content (from "tool" role messages)
      const toolResultMap = new Map<string, string>();
      for (const m of storedMessages) {
        if (m.role === 'tool' && m.tool_call_id) {
          toolResultMap.set(m.tool_call_id, m.content || '');
        }
      }

      const chatMsgs: ChatMessage[] = storedMessages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m) => {
          const msg: ChatMessage = {
            id: `history-${m.id}`,
            role: m.role as 'user' | 'assistant',
            content: m.content || '',
          };
          // Restore toolCalls from assistant messages
          if (m.role === 'assistant' && m.tool_calls) {
            try {
              const rawCalls = JSON.parse(m.tool_calls);
              if (Array.isArray(rawCalls) && rawCalls.length > 0) {
                msg.toolCalls = rawCalls.map((tc: any) => {
                  const name = tc.function?.name || tc.name || '';
                  let input = {};
                  try {
                    input = tc.function?.arguments
                      ? JSON.parse(tc.function.arguments)
                      : tc.arguments || {};
                  } catch { /* ignore */ }
                  // Look up tool result
                  const resultJson = toolResultMap.get(tc.id || '');
                  let status: 'success' | 'error' = 'success';
                  let summary = '';
                  if (resultJson) {
                    try {
                      const result = JSON.parse(resultJson);
                      if (result.status === 'error' || result.error) {
                        status = 'error';
                        summary = (result.error || '').substring(0, 200);
                      } else if (result.message) {
                        summary = result.message.substring(0, 200);
                      } else {
                        summary = resultJson.substring(0, 200);
                      }
                    } catch {
                      summary = resultJson.substring(0, 200);
                    }
                  }
                  return { name, input, status, summary };
                });
              }
            } catch { /* ignore bad JSON */ }
          }
          return msg;
        });
      loadFromHistory(chatMsgs);
    }
  }, [storedMessages, messages.length, loadFromHistory, sessionId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming || !sessionId) return;
    setInput('');
    sendMessage(trimmed);
  };

  const handleInterrupt = async () => {
    if (sessionId) {
      try {
        await chatApi.interrupt(sessionId);
      } catch { /* ignore */ }
    }
    interrupt();
  };

  if (!sessionId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 400 }}>
        <Empty description={t('chat.noSession')} />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
      {/* Messages Area */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 0' }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && messages.length > 0 && messages[messages.length - 1]?.content === '' && !messages[messages.length - 1]?.toolCalls?.length && (
          <div style={{ textAlign: 'center', padding: 16 }}>
            <Spin />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ borderTop: '1px solid #f0f0f0', padding: '12px 0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <FileUploader sessionId={sessionId} />
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            placeholder={t('chat.placeholder')}
            disabled={isStreaming}
            style={{ flex: 1, marginLeft: 8 }}
          />
          {isStreaming ? (
            <Button icon={<StopOutlined />} danger onClick={handleInterrupt} style={{ marginLeft: 8 }}>
              {t('chat.stop')}
            </Button>
          ) : (
            <Button type="primary" icon={<SendOutlined />} onClick={handleSend} style={{ marginLeft: 8 }}>
              {t('chat.send')}
            </Button>
          )}
        </Space.Compact>
      </div>
    </div>
  );
}
