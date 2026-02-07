import { Progress, Space, Tag, Typography } from 'antd';
import type { MigrationTask } from '../../types';
import { getStatusColor } from '../../utils/format';

const { Text } = Typography;

interface Props {
  task: MigrationTask;
}

export default function MigrationProgress({ task }: Props) {
  const total = task.total_items || 1;
  const completed = task.completed_items;
  const failed = task.failed_items;
  const skipped = task.skipped_items;
  const percent = Math.round(((completed + failed + skipped) / total) * 100);

  return (
    <div>
      <Space style={{ marginBottom: 8 }}>
        <Tag color={getStatusColor(task.status)}>{task.status}</Tag>
        <Text type="secondary">
          {completed}/{total} completed
          {failed > 0 && `, ${failed} failed`}
          {skipped > 0 && `, ${skipped} skipped`}
        </Text>
      </Space>
      <Progress
        percent={percent}
        status={task.status === 'failed' ? 'exception' : task.status === 'completed' ? 'success' : 'active'}
        size="small"
      />
    </div>
  );
}
