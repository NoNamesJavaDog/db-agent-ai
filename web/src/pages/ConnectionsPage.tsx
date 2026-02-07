import { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, Tag, Popconfirm, message, List as AntList } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, ApiOutlined, DatabaseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useConnectionStore } from '../stores/useConnectionStore';
import { getDbTypeColor, formatDateTime } from '../utils/format';
import type { Connection, ConnectionCreate, ConnectionUpdate, DatabaseInfo } from '../types';

const DB_TYPES = [
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'MySQL', value: 'mysql' },
  { label: 'GaussDB', value: 'gaussdb' },
  { label: 'Oracle', value: 'oracle' },
  { label: 'SQL Server', value: 'sqlserver' },
];

const DEFAULT_PORTS: Record<string, number> = {
  postgresql: 5432,
  mysql: 3306,
  gaussdb: 5432,
  oracle: 1521,
  sqlserver: 1433,
};

export default function ConnectionsPage() {
  const { t } = useTranslation();
  const { connections, loading, fetch, create, update, remove, activate, test, listDatabases, switchDatabase } = useConnectionStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Connection | null>(null);
  const [form] = Form.useForm();

  // Switch database modal state
  const [dbModalOpen, setDbModalOpen] = useState(false);
  const [dbModalConn, setDbModalConn] = useState<Connection | null>(null);
  const [dbList, setDbList] = useState<DatabaseInfo[]>([]);
  const [dbLoading, setDbLoading] = useState(false);

  useEffect(() => { fetch(); }, [fetch]);

  const handleAdd = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ db_type: 'postgresql', host: 'localhost', port: 5432 });
    setModalOpen(true);
  };

  const handleEdit = (conn: Connection) => {
    setEditing(conn);
    form.setFieldsValue({ ...conn, password: '' });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editing) {
        const data: ConnectionUpdate = { ...values };
        if (!data.password) delete data.password;
        await update(editing.id, data);
        message.success(t('common.success'));
      } else {
        await create(values as ConnectionCreate);
        message.success(t('common.success'));
      }
      setModalOpen(false);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleTest = async (id: number) => {
    const result = await test(id);
    if (result.success) {
      message.success(t('connection.testOk'));
    } else {
      message.error(`${t('connection.testFail')}: ${result.message}`);
    }
  };

  const handleSwitchDb = async (conn: Connection) => {
    setDbModalConn(conn);
    setDbModalOpen(true);
    setDbLoading(true);
    try {
      const result = await listDatabases(conn.id);
      setDbList(result.databases || []);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
      setDbList([]);
    } finally {
      setDbLoading(false);
    }
  };

  const handleSelectDb = async (dbName: string) => {
    if (!dbModalConn) return;
    try {
      await switchDatabase(dbModalConn.id, dbName);
      message.success(`Switched to ${dbName}`);
      setDbModalOpen(false);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  // Group connections by instance (db_type + host:port)
  const groupedConnections = connections.reduce<Record<string, Connection[]>>((acc, conn) => {
    const key = `${conn.db_type}://${conn.host}:${conn.port}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(conn);
    return acc;
  }, {});

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    {
      title: t('connection.dbType'), dataIndex: 'db_type', key: 'db_type',
      render: (v: string) => <Tag color={getDbTypeColor(v)}>{v}</Tag>,
    },
    { title: t('connection.host'), dataIndex: 'host', key: 'host' },
    { title: t('connection.port'), dataIndex: 'port', key: 'port' },
    { title: t('connection.database'), dataIndex: 'database', key: 'database' },
    { title: t('connection.username'), dataIndex: 'username', key: 'username' },
    {
      title: t('common.status'), key: 'status',
      render: (_: any, r: Connection) => (
        <Tag color={r.is_active ? 'green' : 'default'}>
          {r.is_active ? t('connection.active') : t('connection.inactive')}
        </Tag>
      ),
    },
    { title: t('common.created'), dataIndex: 'created_at', key: 'created_at', render: formatDateTime },
    {
      title: t('common.actions'), key: 'actions',
      render: (_: any, r: Connection) => (
        <Space>
          <Button size="small" icon={<ApiOutlined />} onClick={() => handleTest(r.id)}>{t('common.test')}</Button>
          {!r.is_active && (
            <Button size="small" icon={<CheckCircleOutlined />} onClick={() => activate(r.id)}>{t('connection.setActive')}</Button>
          )}
          {r.is_active && (
            <Button size="small" icon={<DatabaseOutlined />} onClick={() => handleSwitchDb(r)}>
              {t('connection.switchDb', 'Switch DB')}
            </Button>
          )}
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)}>{t('common.edit')}</Button>
          <Popconfirm title="Delete?" onConfirm={() => remove(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Render grouped tables
  const instanceKeys = Object.keys(groupedConnections);
  const hasMultipleInstances = instanceKeys.length > 1;

  return (
    <Card
      title={t('connection.title')}
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>{t('common.add')}</Button>}
    >
      {hasMultipleInstances ? (
        instanceKeys.map((instanceKey) => (
          <div key={instanceKey} style={{ marginBottom: 16 }}>
            <Tag color="blue" style={{ marginBottom: 8 }}>{instanceKey}</Tag>
            <Table
              dataSource={groupedConnections[instanceKey]}
              columns={columns}
              rowKey="id"
              loading={loading}
              size="middle"
              pagination={false}
            />
          </div>
        ))
      ) : (
        <Table dataSource={connections} columns={columns} rowKey="id" loading={loading} size="middle" />
      )}

      {/* Add/Edit Connection Modal */}
      <Modal
        title={editing ? t('connection.editTitle') : t('connection.addTitle')}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('common.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="db_type" label={t('connection.dbType')} rules={[{ required: true }]}>
            <Select
              options={DB_TYPES}
              onChange={(v) => form.setFieldsValue({ port: DEFAULT_PORTS[v] || 5432 })}
            />
          </Form.Item>
          <Space style={{ width: '100%' }}>
            <Form.Item name="host" label={t('connection.host')} rules={[{ required: true }]} style={{ flex: 1 }}>
              <Input />
            </Form.Item>
            <Form.Item name="port" label={t('connection.port')} rules={[{ required: true }]}>
              <Input type="number" style={{ width: 120 }} />
            </Form.Item>
          </Space>
          <Form.Item name="database" label={t('connection.database')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label={t('connection.username')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label={t('connection.password')} rules={editing ? [] : [{ required: true }]}>
            <Input.Password placeholder={editing ? 'Leave empty to keep current' : ''} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Switch Database Modal */}
      <Modal
        title={
          <Space>
            <DatabaseOutlined />
            {t('connection.switchDb', 'Switch Database')}
            {dbModalConn && <Tag>{dbModalConn.host}:{dbModalConn.port}</Tag>}
          </Space>
        }
        open={dbModalOpen}
        onCancel={() => setDbModalOpen(false)}
        footer={null}
        width={500}
      >
        <AntList
          loading={dbLoading}
          dataSource={dbList}
          renderItem={(db: DatabaseInfo) => (
            <AntList.Item
              actions={[
                db.is_current
                  ? <Tag color="green">{t('connection.active', 'Current')}</Tag>
                  : <Button type="link" onClick={() => handleSelectDb(db.name)}>{t('connection.setActive', 'Use')}</Button>
              ]}
            >
              <AntList.Item.Meta
                title={db.name}
                description={[db.size, db.owner].filter(Boolean).join(' | ')}
              />
            </AntList.Item>
          )}
        />
      </Modal>
    </Card>
  );
}
