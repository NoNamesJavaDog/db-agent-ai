import { useState } from 'react';
import { Button, Input, InputNumber, Select, DatePicker, Space, Spin } from 'antd';
import { SendOutlined, CloseOutlined, FormOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { chatApi } from '../../api/chat';
import { useChatStore } from '../../stores/useChatStore';
import { useSessionStore } from '../../stores/useSessionStore';
import { useSSEChat } from '../../hooks/useSSEChat';
import type { FormInputRequest } from '../../types';

interface Props {
  msgId: string;
  formRequest: FormInputRequest;
}

export default function FormInputCard({ msgId, formRequest }: Props) {
  const { t } = useTranslation();
  const sessionId = useSessionStore((s) => s.currentSessionId);
  const resolveFormInput = useChatStore((s) => s.resolveFormInput);
  const { sendMessage } = useSSEChat(sessionId);

  const [values, setValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [resolved, setResolved] = useState(false);

  if (!sessionId || resolved) return null;

  const updateField = (name: string, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await chatApi.submitForm(sessionId, values);
      const instruction = res.data.instruction;
      setResolved(true);

      // Build a summary of submitted values
      const summary = formRequest.fields
        .map((f) => `**${f.label}**: ${values[f.name] ?? '-'}`)
        .join('\n');
      resolveFormInput(msgId, `*${t('chat.formSubmitted')}*\n${summary}`);

      // Let AI continue processing
      setTimeout(() => {
        sendMessage(instruction, true);
      }, 300);
    } catch (e: any) {
      resolveFormInput(
        msgId,
        `**Error:** ${e.response?.data?.detail || e.message || 'Failed to submit form'}`
      );
      setResolved(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setResolved(true);
    resolveFormInput(msgId, `*${t('chat.formCancelled')}*`);
  };

  const renderField = (field: typeof formRequest.fields[0]) => {
    const commonStyle = { width: '100%' };

    switch (field.type) {
      case 'text':
        return (
          <Input
            style={commonStyle}
            placeholder={field.placeholder}
            value={values[field.name] || ''}
            onChange={(e) => updateField(field.name, e.target.value)}
          />
        );
      case 'number':
        return (
          <InputNumber
            style={commonStyle}
            placeholder={field.placeholder}
            value={values[field.name]}
            onChange={(v) => updateField(field.name, v)}
          />
        );
      case 'select':
        return (
          <Select
            style={commonStyle}
            placeholder={field.placeholder || t('chat.formSelectPlaceholder')}
            value={values[field.name]}
            onChange={(v) => updateField(field.name, v)}
            options={(field.options || []).map((opt) => ({ value: opt, label: opt }))}
          />
        );
      case 'textarea':
        return (
          <Input.TextArea
            style={commonStyle}
            placeholder={field.placeholder}
            value={values[field.name] || ''}
            onChange={(e) => updateField(field.name, e.target.value)}
            rows={3}
          />
        );
      case 'date':
        return (
          <DatePicker
            style={commonStyle}
            placeholder={field.placeholder}
            onChange={(_date, dateString) => updateField(field.name, dateString)}
          />
        );
      default:
        return (
          <Input
            style={commonStyle}
            placeholder={field.placeholder}
            value={values[field.name] || ''}
            onChange={(e) => updateField(field.name, e.target.value)}
          />
        );
    }
  };

  return (
    <div
      style={{
        margin: '8px 0',
        padding: 12,
        background: '#f0f5ff',
        border: '1px solid #adc6ff',
        borderRadius: 8,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>
        <FormOutlined style={{ marginRight: 6 }} />
        {formRequest.title}
      </div>

      {formRequest.description && (
        <div style={{ marginBottom: 8, color: '#666', fontSize: 13 }}>
          {formRequest.description}
        </div>
      )}

      {formRequest.fields.map((field) => (
        <div key={field.name} style={{ marginBottom: 8 }}>
          <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>
            {field.label}
            {field.required && (
              <span style={{ color: '#ff4d4f', marginLeft: 4, fontSize: 12 }}>
                *{t('chat.formRequired')}
              </span>
            )}
          </div>
          {renderField(field)}
        </div>
      ))}

      {loading ? (
        <Spin size="small" style={{ marginTop: 8 }} />
      ) : (
        <Space style={{ marginTop: 4 }}>
          <Button
            type="primary"
            size="small"
            icon={<SendOutlined />}
            onClick={handleSubmit}
          >
            {t('chat.formSubmit')}
          </Button>
          <Button size="small" icon={<CloseOutlined />} onClick={handleCancel}>
            {t('chat.formCancel')}
          </Button>
        </Space>
      )}
    </div>
  );
}
