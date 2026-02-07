import { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useConnectionStore } from '../../stores/useConnectionStore';
import { useProviderStore } from '../../stores/useProviderStore';

const { Content } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const fetchConnections = useConnectionStore((s) => s.fetch);
  const fetchProviders = useProviderStore((s) => s.fetch);

  useEffect(() => {
    fetchConnections();
    fetchProviders();
  }, [fetchConnections, fetchProviders]);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
      <Layout>
        <Header />
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
