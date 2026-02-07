import { Table, Button, Space, Switch, Tag, Popconfirm } from 'antd';
import { DeleteOutlined, LinkOutlined, EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { McpServer } from '../../types';

interface Props {
  servers: McpServer[];
  loading: boolean;
  onDelete: (name: string) => void;
  onToggle: (name: string, enabled: boolean) => void;
  onConnect: (name: string) => void;
  onViewTools: (name: string) => void;
}

export default function McpServerList({ servers, loading, onDelete, onToggle, onConnect, onViewTools }: Props) {
  const { t } = useTranslation();

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    { title: t('mcp.command'), dataIndex: 'command', key: 'command' },
    {
      title: t('common.status'),
      key: 'status',
      render: (_: any, r: McpServer) => (
        <Space>
          <Switch
            size="small"
            checked={r.enabled}
            onChange={(v) => onToggle(r.name, v)}
          />
          <Tag color={r.connected ? 'green' : 'default'}>
            {r.connected ? t('mcp.connected') : t('mcp.disconnected')}
          </Tag>
        </Space>
      ),
    },
    {
      title: t('mcp.toolCount'),
      dataIndex: 'tool_count',
      key: 'tool_count',
    },
    {
      title: t('common.actions'),
      key: 'actions',
      render: (_: any, r: McpServer) => (
        <Space>
          {!r.connected && r.enabled && (
            <Button size="small" icon={<LinkOutlined />} onClick={() => onConnect(r.name)}>
              {t('common.connect')}
            </Button>
          )}
          {r.connected && (
            <Button size="small" icon={<EyeOutlined />} onClick={() => onViewTools(r.name)}>
              {t('mcp.viewTools')}
            </Button>
          )}
          <Popconfirm title="Delete?" onConfirm={() => onDelete(r.name)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      dataSource={servers}
      columns={columns}
      rowKey="name"
      loading={loading}
      pagination={false}
      size="middle"
    />
  );
}
