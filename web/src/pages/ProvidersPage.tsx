import { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, Tag, Popconfirm, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useProviderStore } from '../stores/useProviderStore';
import { formatDateTime } from '../utils/format';
import type { Provider, ProviderCreate, ProviderUpdate } from '../types';

export default function ProvidersPage() {
  const { t } = useTranslation();
  const { providers, available, loading, fetch, fetchAvailable, create, update, remove, activate } = useProviderStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Provider | null>(null);
  const [form] = Form.useForm();

  useEffect(() => { fetch(); fetchAvailable(); }, [fetch, fetchAvailable]);

  const handleAdd = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (p: Provider) => {
    setEditing(p);
    form.setFieldsValue({ ...p, api_key: '' });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editing) {
        const data: ProviderUpdate = { ...values };
        if (!data.api_key) delete data.api_key;
        await update(editing.id, data);
      } else {
        await create(values as ProviderCreate);
      }
      message.success(t('common.success'));
      setModalOpen(false);
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleProviderTypeChange = (providerType: string) => {
    const info = available.find((a) => a.key === providerType);
    if (info) {
      form.setFieldsValue({ model: info.default_model, base_url: info.base_url || '' });
    }
  };

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    { title: t('provider.providerType'), dataIndex: 'provider', key: 'provider', render: (v: string) => <Tag>{v}</Tag> },
    { title: t('provider.model'), dataIndex: 'model', key: 'model' },
    { title: t('provider.baseUrl'), dataIndex: 'base_url', key: 'base_url', render: (v: string) => v || '-' },
    {
      title: t('common.status'), key: 'status',
      render: (_: any, r: Provider) => (
        <Tag color={r.is_default ? 'green' : 'default'}>
          {r.is_default ? t('provider.default') : '-'}
        </Tag>
      ),
    },
    { title: t('common.created'), dataIndex: 'created_at', key: 'created_at', render: formatDateTime },
    {
      title: t('common.actions'), key: 'actions',
      render: (_: any, r: Provider) => (
        <Space>
          {!r.is_default && (
            <Button size="small" icon={<CheckCircleOutlined />} onClick={() => activate(r.id)}>
              {t('provider.setDefault')}
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

  return (
    <Card
      title={t('provider.title')}
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>{t('common.add')}</Button>}
    >
      <Table dataSource={providers} columns={columns} rowKey="id" loading={loading} size="middle" />

      <Modal
        title={editing ? t('provider.editTitle') : t('provider.addTitle')}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('common.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="provider" label={t('provider.providerType')} rules={[{ required: true }]}>
            <Select
              options={available.map((a) => ({ label: a.name, value: a.key }))}
              onChange={handleProviderTypeChange}
            />
          </Form.Item>
          <Form.Item name="api_key" label={t('provider.apiKey')} rules={editing ? [] : [{ required: true }]}>
            <Input.Password placeholder={editing ? 'Leave empty to keep current' : ''} />
          </Form.Item>
          <Form.Item name="model" label={t('provider.model')}>
            <Input />
          </Form.Item>
          <Form.Item name="base_url" label={t('provider.baseUrl')}>
            <Input placeholder="Optional" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
