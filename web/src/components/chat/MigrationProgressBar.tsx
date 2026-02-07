import { Progress, Space, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ForwardOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { MigrationProgress } from '../../types';

interface Props {
  progress: MigrationProgress;
}

export default function MigrationProgressBar({ progress }: Props) {
  const { t } = useTranslation();
  const { total, completed, failed, skipped } = progress;

  const done = completed + failed + skipped;
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;
  const isFinished = total > 0 && done >= total;
  const hasFailures = failed > 0;

  const status = isFinished
    ? hasFailures ? 'exception' : 'success'
    : 'active';

  return (
    <div style={{ margin: '8px 0', padding: '8px 12px', background: '#fafafa', borderRadius: 8 }}>
      <div style={{ marginBottom: 4, fontWeight: 500, fontSize: 13 }}>
        {t('chat.migrationProgress')}
      </div>
      <Progress
        percent={percent}
        status={status}
        size="small"
        strokeColor={hasFailures ? '#faad14' : undefined}
      />
      <Space size={8} style={{ marginTop: 4, flexWrap: 'wrap' }}>
        <Tag>{t('chat.migrationTotal')}: {total}</Tag>
        <Tag icon={<CheckCircleOutlined />} color="success">
          {t('chat.migrationCompleted')}: {completed}
        </Tag>
        {failed > 0 && (
          <Tag icon={<CloseCircleOutlined />} color="error">
            {t('chat.migrationFailed')}: {failed}
          </Tag>
        )}
        {skipped > 0 && (
          <Tag icon={<ForwardOutlined />} color="warning">
            {t('chat.migrationSkipped')}: {skipped}
          </Tag>
        )}
      </Space>
    </div>
  );
}
