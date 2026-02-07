import { useEffect } from 'react';
import { Card, Button, Space, Tag, Typography, message } from 'antd';
import { PlusOutlined, MessageOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import ChatPanel from '../components/chat/ChatPanel';
import { useSessionStore } from '../stores/useSessionStore';
import { useChatStore } from '../stores/useChatStore';

const { Text } = Typography;

export default function ChatPage() {
  const { t } = useTranslation();
  const { sessions, currentSessionId, fetch, create, activate } = useSessionStore();
  const clearMessages = useChatStore((s) => s.clearMessages);

  useEffect(() => { fetch(); }, [fetch]);

  const handleNewSession = async () => {
    try {
      const session = await create({});
      clearMessages();
      await activate(session.id);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleSwitchSession = async (id: number) => {
    if (id !== currentSessionId) {
      clearMessages();
      await activate(id);
    }
  };

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 160px)' }}>
      {/* Session Sidebar */}
      <Card
        size="small"
        title={t('nav.sessions')}
        extra={<Button type="text" icon={<PlusOutlined />} onClick={handleNewSession} />}
        style={{ width: 260, flexShrink: 0, overflow: 'auto' }}
      >
        {sessions.map((s) => (
          <div
            key={s.id}
            style={{
              cursor: 'pointer',
              background: s.id === currentSessionId ? '#e6f7ff' : 'transparent',
              borderRadius: 6,
              padding: '8px 12px',
              marginBottom: 4,
            }}
            onClick={() => handleSwitchSession(s.id)}
          >
            <Space orientation="vertical" size={0} style={{ width: '100%' }}>
              <Text strong={s.id === currentSessionId} ellipsis>
                <MessageOutlined style={{ marginRight: 4 }} />
                {s.name}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {s.message_count} msgs
                {s.is_current && <Tag color="green" style={{ marginLeft: 4 }}>current</Tag>}
              </Text>
            </Space>
          </div>
        ))}
      </Card>

      {/* Chat Area */}
      <Card style={{ flex: 1 }} styles={{ body: { padding: '0 16px', height: '100%' } }}>
        <ChatPanel />
      </Card>
    </div>
  );
}
