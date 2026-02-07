import { useEffect, useState } from 'react';
import { Card, Button, message } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import McpServerList from '../components/mcp/McpServerList';
import McpServerForm from '../components/mcp/McpServerForm';
import McpToolsDrawer from '../components/mcp/McpToolsDrawer';
import { useMcpStore } from '../stores/useMcpStore';
import { mcpApi } from '../api/mcp';
import type { McpTool } from '../types';

export default function McpPage() {
  const { t } = useTranslation();
  const { servers, loading, fetchServers, addServer, deleteServer, enableServer, disableServer, connectServer } = useMcpStore();
  const [formOpen, setFormOpen] = useState(false);
  const [toolsDrawerOpen, setToolsDrawerOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState('');
  const [serverTools, setServerTools] = useState<McpTool[]>([]);

  useEffect(() => { fetchServers(); }, [fetchServers]);

  const handleAdd = async (values: { name: string; command: string; args: string; env: string }) => {
    const args = values.args ? values.args.split(',').map((s) => s.trim()) : [];
    const env: Record<string, string> = {};
    if (values.env) {
      values.env.split('\n').forEach((line) => {
        const idx = line.indexOf('=');
        if (idx > 0) env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
      });
    }
    try {
      await addServer({ name: values.name, command: values.command, args, env: Object.keys(env).length ? env : undefined });
      message.success(t('common.success'));
      setFormOpen(false);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleToggle = async (name: string, enabled: boolean) => {
    if (enabled) {
      await enableServer(name);
    } else {
      await disableServer(name);
    }
  };

  const handleConnect = async (name: string) => {
    try {
      await connectServer(name);
      message.success(t('common.success'));
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleViewTools = async (name: string) => {
    try {
      const res = await mcpApi.getServerTools(name);
      setSelectedServer(name);
      setServerTools(res.data);
      setToolsDrawerOpen(true);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  return (
    <Card
      title={t('mcp.title')}
      extra={
        <>
          <Button icon={<ReloadOutlined />} onClick={fetchServers} style={{ marginRight: 8 }}>{t('common.refresh')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>{t('common.add')}</Button>
        </>
      }
    >
      <McpServerList
        servers={servers}
        loading={loading}
        onDelete={deleteServer}
        onToggle={handleToggle}
        onConnect={handleConnect}
        onViewTools={handleViewTools}
      />
      <McpServerForm open={formOpen} onCancel={() => setFormOpen(false)} onSubmit={handleAdd} />
      <McpToolsDrawer
        open={toolsDrawerOpen}
        serverName={selectedServer}
        tools={serverTools}
        onClose={() => setToolsDrawerOpen(false)}
      />
    </Card>
  );
}
