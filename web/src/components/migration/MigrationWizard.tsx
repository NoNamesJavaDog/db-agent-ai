import { useState } from 'react';
import { Modal, Steps, Form, Input, Select } from 'antd';
import { useTranslation } from 'react-i18next';
import { useConnectionStore } from '../../stores/useConnectionStore';
import type { MigrationTaskCreate } from '../../types';

interface Props {
  open: boolean;
  onCancel: () => void;
  onSubmit: (data: MigrationTaskCreate) => void;
}

export default function MigrationWizard({ open, onCancel, onSubmit }: Props) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  const [form] = Form.useForm();
  const connections = useConnectionStore((s) => s.connections);

  const handleFinish = () => {
    form.validateFields().then((values) => {
      onSubmit({
        name: values.name,
        source_connection_id: values.source_connection_id,
        target_connection_id: values.target_connection_id,
        source_schema: values.source_schema || undefined,
        target_schema: values.target_schema || undefined,
      });
      form.resetFields();
      setStep(0);
    });
  };

  const steps = [
    { title: t('migration.sourceConn') },
    { title: t('migration.targetConn') },
    { title: t('common.confirm') },
  ];

  return (
    <Modal
      title={t('migration.createTask')}
      open={open}
      onCancel={() => { onCancel(); setStep(0); }}
      onOk={step === 2 ? handleFinish : () => setStep(step + 1)}
      okText={step === 2 ? t('common.confirm') : undefined}
      width={600}
    >
      <Steps current={step} items={steps} style={{ marginBottom: 24 }} />
      <Form form={form} layout="vertical">
        {step === 0 && (
          <>
            <Form.Item name="name" label={t('common.name')} rules={[{ required: true }]}>
              <Input placeholder="Migration task name" />
            </Form.Item>
            <Form.Item name="source_connection_id" label={t('migration.sourceConn')} rules={[{ required: true }]}>
              <Select
                options={connections.map((c) => ({ label: `${c.name} (${c.db_type})`, value: c.id }))}
                placeholder="Select source"
              />
            </Form.Item>
            <Form.Item name="source_schema" label={t('migration.sourceSchema')}>
              <Input placeholder="Optional schema" />
            </Form.Item>
          </>
        )}
        {step === 1 && (
          <>
            <Form.Item name="target_connection_id" label={t('migration.targetConn')} rules={[{ required: true }]}>
              <Select
                options={connections.map((c) => ({ label: `${c.name} (${c.db_type})`, value: c.id }))}
                placeholder="Select target"
              />
            </Form.Item>
            <Form.Item name="target_schema" label={t('migration.targetSchema')}>
              <Input placeholder="Optional schema" />
            </Form.Item>
          </>
        )}
        {step === 2 && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <p>Review and confirm migration task creation.</p>
          </div>
        )}
      </Form>
    </Modal>
  );
}
