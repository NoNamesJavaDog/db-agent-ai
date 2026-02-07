import { Drawer, Typography } from 'antd';
import { ToolOutlined } from '@ant-design/icons';
import type { McpTool } from '../../types';

const { Text, Paragraph } = Typography;

interface Props {
  open: boolean;
  serverName: string;
  tools: McpTool[];
  onClose: () => void;
}

export default function McpToolsDrawer({ open, serverName, tools, onClose }: Props) {
  return (
    <Drawer
      title={`Tools - ${serverName}`}
      open={open}
      onClose={onClose}
      width={500}
    >
      {tools.map((tool) => (
        <div key={tool.name} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
          <ToolOutlined style={{ fontSize: 20, marginTop: 4 }} />
          <div style={{ flex: 1 }}>
            <Text strong>{tool.name}</Text>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              {tool.description || 'No description'}
            </Paragraph>
            {tool.input_schema && (
              <pre style={{ fontSize: 11, background: '#f6f8fa', padding: 8, borderRadius: 4, marginTop: 4, maxHeight: 100, overflow: 'auto' }}>
                {JSON.stringify(tool.input_schema, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </Drawer>
  );
}
