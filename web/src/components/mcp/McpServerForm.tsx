import { Modal, Form, Input } from 'antd';
import { useTranslation } from 'react-i18next';

interface Props {
  open: boolean;
  onCancel: () => void;
  onSubmit: (values: { name: string; command: string; args: string; env: string }) => void;
}

export default function McpServerForm({ open, onCancel, onSubmit }: Props) {
  const { t } = useTranslation();
  const [form] = Form.useForm();

  const handleOk = () => {
    form.validateFields().then((values) => {
      onSubmit(values);
      form.resetFields();
    });
  };

  return (
    <Modal title={t('mcp.addTitle')} open={open} onCancel={onCancel} onOk={handleOk}>
      <Form form={form} layout="vertical">
        <Form.Item name="name" label={t('common.name')} rules={[{ required: true }]}>
          <Input placeholder="e.g. filesystem" />
        </Form.Item>
        <Form.Item name="command" label={t('mcp.command')} rules={[{ required: true }]}>
          <Input placeholder="e.g. npx" />
        </Form.Item>
        <Form.Item name="args" label={t('mcp.args')}>
          <Input placeholder="Comma-separated, e.g. -y,@modelcontextprotocol/server-filesystem,/tmp" />
        </Form.Item>
        <Form.Item name="env" label={t('mcp.env')}>
          <Input.TextArea rows={3} placeholder="KEY=VALUE per line" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
