import { useEffect, useState } from 'react';
import { Card, Table, Button, Space, Tag, Popconfirm, Modal, Input, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, MessageOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSessionStore } from '../stores/useSessionStore';
import { formatDateTime } from '../utils/format';
import type { Session } from '../types';

export default function SessionsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { sessions, loading, fetch, create, remove, rename, activate, reset } = useSessionStore();
  const [renameModal, setRenameModal] = useState(false);
  const [renameTarget, setRenameTarget] = useState<Session | null>(null);
  const [newName, setNewName] = useState('');

  useEffect(() => { fetch(); }, [fetch]);

  const handleNew = async () => {
    try {
      const session = await create({});
      message.success(t('common.success'));
      await activate(session.id);
      navigate('/chat');
    } catch (e: any) {
      message.error(e.response?.data?.detail || t('common.error'));
    }
  };

  const handleSwitch = async (session: Session) => {
    await activate(session.id);
    navigate('/chat');
  };

  const handleRename = (session: Session) => {
    setRenameTarget(session);
    setNewName(session.name);
    setRenameModal(true);
  };

  const submitRename = async () => {
    if (renameTarget && newName.trim()) {
      await rename(renameTarget.id, newName.trim());
      message.success(t('common.success'));
      setRenameModal(false);
    }
  };

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    {
      title: t('session.messageCount'), dataIndex: 'message_count', key: 'message_count',
      render: (v: number) => <Tag>{v}</Tag>,
    },
    {
      title: t('common.status'), key: 'status',
      render: (_: any, r: Session) => r.is_current ? <Tag color="green">{t('session.current')}</Tag> : null,
    },
    { title: t('common.created'), dataIndex: 'created_at', key: 'created_at', render: formatDateTime, sorter: (a: Session, b: Session) => (a.created_at || '').localeCompare(b.created_at || ''), defaultSortOrder: 'descend' as const },
    {
      title: t('common.actions'), key: 'actions',
      render: (_: any, r: Session) => (
        <Space>
          <Button size="small" icon={<MessageOutlined />} onClick={() => handleSwitch(r)}>
            {t('session.switchTo')}
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleRename(r)}>
            {t('session.rename')}
          </Button>
          <Popconfirm title="Reset conversation?" onConfirm={() => reset(r.id)}>
            <Button size="small" icon={<ReloadOutlined />}>{t('session.reset')}</Button>
          </Popconfirm>
          <Popconfirm title="Delete?" onConfirm={() => remove(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={t('session.title')}
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleNew}>{t('session.newSession')}</Button>}
    >
      <Table dataSource={sessions} columns={columns} rowKey="id" loading={loading} size="middle" />

      <Modal title={t('session.rename')} open={renameModal} onCancel={() => setRenameModal(false)} onOk={submitRename}>
        <Input value={newName} onChange={(e) => setNewName(e.target.value)} />
      </Modal>
    </Card>
  );
}
