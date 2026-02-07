import { Layout, Menu } from 'antd';
import {
  MessageOutlined,
  DatabaseOutlined,
  ApiOutlined,
  HistoryOutlined,
  CloudServerOutlined,
  ThunderboltOutlined,
  SwapOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const { Sider } = Layout;

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
}

export default function Sidebar({ collapsed, onCollapse }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const items = [
    { key: '/chat', icon: <MessageOutlined />, label: t('nav.chat') },
    { key: '/connections', icon: <DatabaseOutlined />, label: t('nav.connections') },
    { key: '/providers', icon: <ApiOutlined />, label: t('nav.providers') },
    { key: '/sessions', icon: <HistoryOutlined />, label: t('nav.sessions') },
    { key: '/mcp', icon: <CloudServerOutlined />, label: t('nav.mcp') },
    { key: '/skills', icon: <ThunderboltOutlined />, label: t('nav.skills') },
    { key: '/migration', icon: <SwapOutlined />, label: t('nav.migration') },
    { key: '/settings', icon: <SettingOutlined />, label: t('nav.settings') },
  ];

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      style={{ minHeight: '100vh' }}
      theme="light"
    >
      <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: collapsed ? 14 : 18 }}>
        {collapsed ? 'DB' : 'DB Agent AI'}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={items}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  );
}
