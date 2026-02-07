import { Avatar, Space } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import MarkdownRenderer from './MarkdownRenderer';
import ToolCallCard from './ToolCallCard';
import PendingCard from './PendingCard';
import MigrationCard from './MigrationCard';
import MigrationProgressBar from './MigrationProgressBar';
import FormInputCard from './FormInputCard';
import type { ChatMessage } from '../../types';

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: 12,
        marginBottom: 16,
        alignItems: 'flex-start',
      }}
    >
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{ background: isUser ? '#1890ff' : '#87d068', flexShrink: 0 }}
      />
      <div
        style={{
          maxWidth: '75%',
          background: isUser ? '#e6f7ff' : '#fff',
          padding: '12px 16px',
          borderRadius: 12,
          border: '1px solid #f0f0f0',
          minWidth: 60,
        }}
      >
        {isUser ? (
          <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
        ) : (
          <>
            {message.parts && message.parts.length > 0 ? (
              message.parts.map((part, i) =>
                part.type === 'text' ? (
                  <MarkdownRenderer key={`text-${i}`} content={part.content} />
                ) : (
                  message.toolCalls?.[part.toolIndex] && (
                    <div key={`tool-${i}`} style={{ margin: '8px 0' }}>
                      <ToolCallCard toolCall={message.toolCalls[part.toolIndex]} />
                    </div>
                  )
                )
              )
            ) : (
              <>
                {message.toolCalls && message.toolCalls.length > 0 && (
                  <Space orientation="vertical" style={{ width: '100%', marginBottom: 8 }}>
                    {message.toolCalls.map((tc, i) => (
                      <ToolCallCard key={`${tc.name}-${i}`} toolCall={tc} />
                    ))}
                  </Space>
                )}
                {message.content && <MarkdownRenderer content={message.content} />}
              </>
            )}
            {message.migrationProgress && (
              <MigrationProgressBar progress={message.migrationProgress} />
            )}
            {message.pending && message.pending.length > 0 && (
              <PendingCard msgId={message.id} operations={message.pending} />
            )}
            {message.migrationSetup && (
              <MigrationCard msgId={message.id} setup={message.migrationSetup} />
            )}
            {message.formInput && (
              <FormInputCard msgId={message.id} formRequest={message.formInput} />
            )}
            {message.isStreaming && !message.content && !message.toolCalls?.length && (
              <span style={{ color: '#999' }}>Thinking...</span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
