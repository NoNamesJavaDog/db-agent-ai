import { Card, Tag, Typography } from 'antd';
import {
  ToolOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { ToolCall } from '../../types';

const { Text, Paragraph } = Typography;

interface Props {
  toolCall: ToolCall;
}

export default function ToolCallCard({ toolCall }: Props) {
  const statusIcon = {
    running: <LoadingOutlined spin style={{ color: '#1890ff' }} />,
    success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
  };

  const statusColor = {
    running: 'processing',
    success: 'success',
    error: 'error',
  } as const;

  return (
    <Card
      size="small"
      style={{ margin: '8px 0', background: '#f9f9f9' }}
      title={
        <span>
          <ToolOutlined style={{ marginRight: 8 }} />
          <Text strong>{toolCall.name}</Text>
          <Tag color={statusColor[toolCall.status || 'running']} style={{ marginLeft: 8 }}>
            {statusIcon[toolCall.status || 'running']} {toolCall.status || 'running'}
          </Tag>
        </span>
      }
    >
      {Object.keys(toolCall.input).length > 0 && (
        <Paragraph style={{ margin: 0 }}>
          <pre style={{ fontSize: 12, margin: 0, background: '#f0f0f0', padding: 8, borderRadius: 4, maxHeight: 120, overflow: 'auto' }}>
            {JSON.stringify(toolCall.input, null, 2)}
          </pre>
        </Paragraph>
      )}
      {toolCall.summary && (
        <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 12 }}>
          {toolCall.summary}
        </Paragraph>
      )}
    </Card>
  );
}
