import { useState, useEffect, useMemo } from 'react';
import { Button, Select, Input, Switch, Space, Spin } from 'antd';
import { CloseOutlined, SwapRightOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { chatApi } from '../../api/chat';
import { useChatStore } from '../../stores/useChatStore';
import { useSessionStore } from '../../stores/useSessionStore';
import { useConnectionStore } from '../../stores/useConnectionStore';
import { useSSEChat } from '../../hooks/useSSEChat';
import type { MigrationSetup } from '../../types';

interface Props {
  msgId: string;
  setup: MigrationSetup;
}

export default function MigrationCard({ msgId, setup }: Props) {
  const { t } = useTranslation();
  const sessionId = useSessionStore((s) => s.currentSessionId);
  const resolveMigrationSetup = useChatStore((s) => s.resolveMigrationSetup);
  const { sendMessage } = useSSEChat(sessionId);
  const connections = useConnectionStore((s) => s.connections);
  const fetchConnections = useConnectionStore((s) => s.fetch);

  const [sourceId, setSourceId] = useState<number | undefined>();
  const [targetId, setTargetId] = useState<number | undefined>();
  const [sourceSchema, setSourceSchema] = useState('');
  const [targetSchema, setTargetSchema] = useState('');
  const [autoExecute, setAutoExecute] = useState(true);
  const [loading, setLoading] = useState(false);
  const [resolved, setResolved] = useState(false);

  // Fetch connections on mount
  useEffect(() => {
    if (connections.length === 0) {
      fetchConnections();
    }
  }, [connections.length, fetchConnections]);

  // Auto-select connections matching suggested db types
  useEffect(() => {
    if (connections.length === 0) return;
    if (setup.suggested_source_db_type && !sourceId) {
      const match = connections.find(
        (c) => c.db_type.toLowerCase() === setup.suggested_source_db_type!.toLowerCase()
      );
      if (match) setSourceId(match.id);
    }
    if (setup.suggested_target_db_type && !targetId) {
      const match = connections.find(
        (c) => c.db_type.toLowerCase() === setup.suggested_target_db_type!.toLowerCase()
      );
      if (match) setTargetId(match.id);
    }
  }, [connections, setup.suggested_source_db_type, setup.suggested_target_db_type, sourceId, targetId]);

  const connectionOptions = useMemo(
    () =>
      connections.map((c) => ({
        value: c.id,
        label: `${c.name} (${c.db_type} - ${c.host}:${c.port}/${c.database})`,
      })),
    [connections]
  );

  if (!sessionId || resolved) return null;

  const handleStart = async () => {
    if (!sourceId || !targetId) return;
    setLoading(true);
    try {
      const res = await chatApi.startMigration(sessionId, {
        source_connection_id: sourceId,
        target_connection_id: targetId,
        source_schema: sourceSchema || undefined,
        target_schema: targetSchema || undefined,
        auto_execute: autoExecute,
      });
      const { instruction, task_id } = res.data;
      setResolved(true);
      resolveMigrationSetup(msgId, `*${t('chat.migrationStarting')} (Task #${task_id})*`);
      // Send the instruction to the AI
      setTimeout(() => {
        sendMessage(instruction, true);
      }, 300);
    } catch (e: any) {
      resolveMigrationSetup(
        msgId,
        `**Error:** ${e.response?.data?.detail || e.message || 'Failed to start migration'}`
      );
      setResolved(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setResolved(true);
    resolveMigrationSetup(msgId, `*${t('chat.migrationCancelled')}*`);
  };

  return (
    <div
      style={{
        margin: '8px 0',
        padding: 12,
        background: '#e6f4ff',
        border: '1px solid #91caff',
        borderRadius: 8,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        <SwapRightOutlined style={{ marginRight: 6 }} />
        {t('chat.migrationTitle')}
      </div>

      {setup.reason && (
        <div style={{ marginBottom: 8, color: '#666', fontSize: 13 }}>
          {setup.reason}
        </div>
      )}

      <div style={{ marginBottom: 8 }}>
        <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>{t('chat.migrationSource')}</div>
        <Select
          style={{ width: '100%' }}
          placeholder={t('chat.migrationSelectSource')}
          value={sourceId}
          onChange={setSourceId}
          options={connectionOptions}
        />
      </div>

      <div style={{ marginBottom: 8 }}>
        <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>{t('chat.migrationTarget')}</div>
        <Select
          style={{ width: '100%' }}
          placeholder={t('chat.migrationSelectTarget')}
          value={targetId}
          onChange={setTargetId}
          options={connectionOptions}
        />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: 4, fontSize: 13, color: '#666' }}>{t('chat.migrationSourceSchema')}</div>
          <Input
            size="small"
            value={sourceSchema}
            onChange={(e) => setSourceSchema(e.target.value)}
          />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: 4, fontSize: 13, color: '#666' }}>{t('chat.migrationTargetSchema')}</div>
          <Input
            size="small"
            value={targetSchema}
            onChange={(e) => setTargetSchema(e.target.value)}
          />
        </div>
      </div>

      <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Switch size="small" checked={autoExecute} onChange={setAutoExecute} />
        <span style={{ fontSize: 13 }}>{t('chat.migrationAutoExecute')}</span>
        <span style={{ fontSize: 12, color: '#999' }}>({t('chat.migrationAutoExecuteDesc')})</span>
      </div>

      {loading ? (
        <Spin size="small" style={{ marginTop: 8 }} />
      ) : (
        <Space style={{ marginTop: 4 }}>
          <Button
            type="primary"
            size="small"
            icon={<SwapRightOutlined />}
            onClick={handleStart}
            disabled={!sourceId || !targetId}
          >
            {t('chat.migrationStart')}
          </Button>
          <Button size="small" icon={<CloseOutlined />} onClick={handleCancel}>
            {t('chat.migrationCancel')}
          </Button>
        </Space>
      )}
    </div>
  );
}
