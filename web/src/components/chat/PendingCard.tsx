import { useState } from 'react';
import { Button, Tag, Space, Spin } from 'antd';
import { CloseOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { chatApi } from '../../api/chat';
import { useChatStore } from '../../stores/useChatStore';
import { useSessionStore } from '../../stores/useSessionStore';
import { useSSEChat } from '../../hooks/useSSEChat';
import type { PendingOperation } from '../../types';

interface Props {
  msgId: string;
  operations: PendingOperation[];
}

export default function PendingCard({ msgId, operations }: Props) {
  const { t } = useTranslation();
  const sessionId = useSessionStore((s) => s.currentSessionId);
  const resolvePending = useChatStore((s) => s.resolvePending);
  const { sendMessage } = useSSEChat(sessionId);
  const [loading, setLoading] = useState(false);
  const [resolved, setResolved] = useState(false);

  if (!sessionId || resolved) return null;

  const handleConfirmAll = async () => {
    setLoading(true);
    try {
      const res = await chatApi.confirmAll(sessionId);
      const results = res.data?.results || [];
      const hasError = results.some((r: any) => r.status === 'error' || r.error);

      // Format result text
      const lines = results.map((r: any, i: number) => {
        if (r.error) return `${i + 1}. ❌ ${r.error}`;
        if (r.status === 'error') return `${i + 1}. ❌ ${r.error || 'Failed'}`;
        if (r.rows_affected !== undefined) return `${i + 1}. ✅ ${r.rows_affected} rows affected`;
        return `${i + 1}. ✅ Success`;
      });
      const resultText = `**Execution Result:**\n${lines.join('\n')}`;

      setResolved(true);
      resolvePending(msgId, resultText);

      // Auto-send result to AI to continue the task
      if (hasError) {
        const errorDetail = results
          .filter((r: any) => r.status === 'error' || r.error)
          .map((r: any) => r.error || 'Unknown error')
          .join('; ');
        setTimeout(() => {
          sendMessage(
            `SQL execution failed with error: ${errorDetail}. Please analyze the error, fix the SQL, and continue the task.`,
            true
          );
        }, 500);
      } else {
        // Success — tell AI to continue
        setTimeout(() => {
          sendMessage('ok', true);
        }, 500);
      }
    } catch (e: any) {
      resolvePending(msgId, `**Error:** ${e.message || 'Confirm failed'}`);
      setResolved(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipAll = async () => {
    setLoading(true);
    try {
      await chatApi.skipAll(sessionId);
      setResolved(true);
      resolvePending(msgId, '*Operations skipped.*');
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      margin: '8px 0',
      padding: 12,
      background: '#fffbe6',
      border: '1px solid #ffe58f',
      borderRadius: 8,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        ⚠️ {t('chat.pendingTitle')} ({operations.length})
      </div>
      {operations.map((op, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <Space style={{ marginBottom: 4 }}>
            <Tag color="orange">{op.type}</Tag>
            {op.description && <span style={{ color: '#666', fontSize: 12 }}>{op.description}</span>}
          </Space>
          {op.sql && (
            <pre style={{
              background: '#f6f8fa',
              padding: 8,
              borderRadius: 4,
              fontSize: 12,
              overflow: 'auto',
              maxHeight: 150,
              margin: 0,
            }}>
              {op.sql}
            </pre>
          )}
        </div>
      ))}
      {loading ? (
        <Spin size="small" style={{ marginTop: 8 }} />
      ) : (
        <Space style={{ marginTop: 8 }}>
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={handleConfirmAll}
          >
            {t('chat.confirmAll')}
          </Button>
          <Button
            size="small"
            icon={<CloseOutlined />}
            onClick={handleSkipAll}
          >
            {t('chat.skipAll')}
          </Button>
        </Space>
      )}
    </div>
  );
}
