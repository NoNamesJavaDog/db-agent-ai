import { Table, Tag, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { Skill } from '../../types';

interface Props {
  skills: Skill[];
  loading: boolean;
  onViewDetail: (name: string) => void;
}

export default function SkillList({ skills, loading, onViewDetail }: Props) {
  const { t } = useTranslation();

  const columns = [
    { title: t('common.name'), dataIndex: 'name', key: 'name' },
    {
      title: t('skill.source'),
      dataIndex: 'source',
      key: 'source',
      render: (v: string) => <Tag color={v === 'personal' ? 'blue' : 'green'}>{v}</Tag>,
    },
    {
      title: t('skill.userInvocable'),
      dataIndex: 'user_invocable',
      key: 'user_invocable',
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Yes' : 'No'}</Tag>,
    },
    {
      title: t('skill.modelInvocable'),
      dataIndex: 'model_invocable',
      key: 'model_invocable',
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Yes' : 'No'}</Tag>,
    },
    {
      title: t('common.actions'),
      key: 'actions',
      render: (_: any, r: Skill) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => onViewDetail(r.name)}>
          Detail
        </Button>
      ),
    },
  ];

  return (
    <Table
      dataSource={skills}
      columns={columns}
      rowKey="name"
      loading={loading}
      pagination={false}
      size="middle"
    />
  );
}
