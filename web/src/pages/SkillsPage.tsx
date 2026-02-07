import { useEffect, useState } from 'react';
import { Card, Button, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import SkillList from '../components/skills/SkillList';
import SkillDetailDrawer from '../components/skills/SkillDetailDrawer';
import { useSkillStore } from '../stores/useSkillStore';
import type { SkillDetail } from '../types';

export default function SkillsPage() {
  const { t } = useTranslation();
  const { skills, loading, fetch, reload, getDetail } = useSkillStore();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);

  useEffect(() => { fetch(); }, [fetch]);

  const handleReload = async () => {
    await reload();
    message.success(t('common.success'));
  };

  const handleViewDetail = async (name: string) => {
    const detail = await getDetail(name);
    setSelectedSkill(detail);
    setDrawerOpen(true);
  };

  return (
    <Card
      title={t('skill.title')}
      extra={
        <Button icon={<ReloadOutlined />} onClick={handleReload}>
          {t('skill.reload')}
        </Button>
      }
    >
      <SkillList skills={skills} loading={loading} onViewDetail={handleViewDetail} />
      <SkillDetailDrawer open={drawerOpen} skill={selectedSkill} onClose={() => setDrawerOpen(false)} />
    </Card>
  );
}
