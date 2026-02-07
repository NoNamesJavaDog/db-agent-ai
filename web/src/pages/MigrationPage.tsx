import { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, Space, Popconfirm, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import MigrationWizard from '../components/migration/MigrationWizard';
import MigrationProgress from '../components/migration/MigrationProgress';
import { useConnectionStore } from '../stores/useConnectionStore';
import { formatDateTime, getStatusColor } from '../utils/format';
import apiClient from '../api/client';
import type { MigrationTask, MigrationTaskCreate, MigrationItem } from '../types';

export default function MigrationPage() {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState<MigrationTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Record<number, MigrationItem[]>>({});
  const fetchConnections = useConnectionStore((s) => s.fetch);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<MigrationTask[]>('/migration/tasks');
      setTasks(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    fetchConnections();
  }, [fetchConnections]);

  const handleCreate = async (data: MigrationTaskCreate) => {
    try {
      await apiClient.post('/migration/tasks', data);
      message.success(t('common.success'));
      setWizardOpen(false);
      fetchTasks();
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleDelete = async (id: number) => {
    await apiClient.delete(`/migration/tasks/${id}`);
    fetchTasks();
  };

  const loadItems = async (taskId: number) => {
    const res = await apiClient.get<MigrationItem[]>(`/migration/tasks/${taskId}/items`);
    setExpandedItems((prev) => ({ ...prev, [taskId]: res.data }));
  };

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    {
      title: t('migration.sourceConn'), key: 'source',
      render: (_: any, r: MigrationTask) => <Tag>{r.source_db_type}</Tag>,
    },
    {
      title: t('migration.targetConn'), key: 'target',
      render: (_: any, r: MigrationTask) => <Tag>{r.target_db_type}</Tag>,
    },
    {
      title: t('common.status'), dataIndex: 'status', key: 'status',
      render: (v: string) => <Tag color={getStatusColor(v)}>{v}</Tag>,
    },
    {
      title: t('migration.progress'), key: 'progress',
      render: (_: any, r: MigrationTask) => <MigrationProgress task={r} />,
      width: 250,
    },
    { title: t('common.created'), dataIndex: 'created_at', key: 'created_at', render: formatDateTime },
    {
      title: t('common.actions'), key: 'actions',
      render: (_: any, r: MigrationTask) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => loadItems(r.id)}>
            {t('migration.items')}
          </Button>
          <Popconfirm title="Delete?" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const itemColumns = [
    { title: 'Type', dataIndex: 'object_type', key: 'object_type' },
    { title: 'Name', dataIndex: 'object_name', key: 'object_name' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={getStatusColor(v)}>{v}</Tag> },
    { title: 'Order', dataIndex: 'execution_order', key: 'execution_order' },
    { title: 'Error', dataIndex: 'error_message', key: 'error_message', render: (v: string) => v || '-' },
  ];

  return (
    <Card
      title={t('migration.title')}
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setWizardOpen(true)}>{t('migration.createTask')}</Button>}
    >
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={loading}
        size="middle"
        expandable={{
          expandedRowRender: (record) => {
            const items = expandedItems[record.id];
            if (!items) return <p>Loading...</p>;
            return <Table dataSource={items} columns={itemColumns} rowKey="id" size="small" pagination={false} />;
          },
          onExpand: (expanded, record) => {
            if (expanded && !expandedItems[record.id]) {
              loadItems(record.id);
            }
          },
        }}
      />
      <MigrationWizard open={wizardOpen} onCancel={() => setWizardOpen(false)} onSubmit={handleCreate} />
    </Card>
  );
}
