import { Layout, Space, Dropdown, Tag, message } from 'antd';
import { DatabaseOutlined, ApiOutlined, SwapOutlined } from '@ant-design/icons';
import { useConnectionStore } from '../../stores/useConnectionStore';
import { useProviderStore } from '../../stores/useProviderStore';
import { getDbTypeColor } from '../../utils/format';

const { Header: AntHeader } = Layout;

export default function Header() {
  const connections = useConnectionStore((s) => s.connections);
  const activateConn = useConnectionStore((s) => s.activate);
  const providers = useProviderStore((s) => s.providers);
  const activateProvider = useProviderStore((s) => s.activate);

  const activeConn = connections.find((c) => c.is_active);
  const defaultProvider = providers.find((p) => p.is_default);

  const connItems = connections.map((c) => ({
    key: String(c.id),
    label: (
      <Space>
        <Tag color={getDbTypeColor(c.db_type)} style={{ margin: 0 }}>{c.db_type}</Tag>
        <span>{c.name}</span>
        <span style={{ color: '#999', fontSize: 12 }}>{c.host}:{c.port}/{c.database}</span>
        {c.is_active && <Tag color="green" style={{ margin: 0 }}>active</Tag>}
      </Space>
    ),
    disabled: c.is_active,
  }));

  const providerItems = providers.map((p) => ({
    key: String(p.id),
    label: (
      <Space>
        <span>{p.name}</span>
        <span style={{ color: '#999', fontSize: 12 }}>{p.model}</span>
        {p.is_default && <Tag color="green" style={{ margin: 0 }}>default</Tag>}
      </Space>
    ),
    disabled: p.is_default,
  }));

  const handleConnSwitch = async ({ key }: { key: string }) => {
    try {
      await activateConn(Number(key));
      message.success('Database switched');
    } catch {
      message.error('Switch failed');
    }
  };

  const handleProviderSwitch = async ({ key }: { key: string }) => {
    try {
      await activateProvider(Number(key));
      message.success('Provider switched');
    } catch {
      message.error('Switch failed');
    }
  };

  return (
    <AntHeader style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0' }}>
      <Space size="middle">
        <Dropdown menu={{ items: connItems, onClick: handleConnSwitch }} trigger={['click']}>
          <Tag icon={<DatabaseOutlined />} color="blue" style={{ cursor: 'pointer' }}>
            {activeConn ? `${activeConn.name} (${activeConn.db_type})` : 'No Connection'} <SwapOutlined />
          </Tag>
        </Dropdown>
        <Dropdown menu={{ items: providerItems, onClick: handleProviderSwitch }} trigger={['click']}>
          <Tag icon={<ApiOutlined />} color="green" style={{ cursor: 'pointer' }}>
            {defaultProvider ? `${defaultProvider.name} (${defaultProvider.model})` : 'No Provider'} <SwapOutlined />
          </Tag>
        </Dropdown>
      </Space>
    </AntHeader>
  );
}
