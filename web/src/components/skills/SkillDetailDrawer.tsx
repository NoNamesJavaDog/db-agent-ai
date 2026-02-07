import { Drawer, Tag, Space, Typography } from 'antd';
import MarkdownRenderer from '../chat/MarkdownRenderer';
import type { SkillDetail } from '../../types';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

interface Props {
  open: boolean;
  skill: SkillDetail | null;
  onClose: () => void;
}

export default function SkillDetailDrawer({ open, skill, onClose }: Props) {
  const { t } = useTranslation();

  return (
    <Drawer title={skill?.name || ''} open={open} onClose={onClose} width={600}>
      {skill && (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Tag color={skill.source === 'personal' ? 'blue' : 'green'}>{skill.source}</Tag>
            {skill.user_invocable && <Tag color="cyan">{t('skill.userInvocable')}</Tag>}
            {skill.model_invocable && <Tag color="purple">{t('skill.modelInvocable')}</Tag>}
          </Space>
          {skill.description && (
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              {skill.description}
            </Text>
          )}
          <div style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, background: '#fafafa' }}>
            <MarkdownRenderer content={skill.instructions} />
          </div>
        </div>
      )}
    </Drawer>
  );
}
