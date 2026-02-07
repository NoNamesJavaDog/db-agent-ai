import { useEffect, useState } from 'react';
import { Card, Form, Select, message, Descriptions } from 'antd';
import { useTranslation } from 'react-i18next';
import { settingsApi } from '../api/settings';
import apiClient from '../api/client';
import type { Settings, HealthStatus } from '../types';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const [settings, setSettings] = useState<Settings>({ language: 'zh', theme: 'light' });
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const fetchSettings = async () => {
    const res = await settingsApi.get();
    setSettings(res.data);
    i18n.changeLanguage(res.data.language);
  };

  const fetchHealth = async () => {
    try {
      const res = await apiClient.get<HealthStatus>('/health');
      setHealth(res.data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchHealth();
  }, []);

  const handleLanguageChange = async (lang: string) => {
    await settingsApi.update({ language: lang });
    i18n.changeLanguage(lang);
    setSettings((s) => ({ ...s, language: lang }));
    message.success(t('common.success'));
  };

  const handleThemeChange = async (theme: string) => {
    await settingsApi.update({ theme });
    setSettings((s) => ({ ...s, theme }));
    message.success(t('common.success'));
  };

  return (
    <div>
      <Card title={t('settings.title')} style={{ marginBottom: 16 }}>
        <Form layout="vertical" style={{ maxWidth: 400 }}>
          <Form.Item label={t('settings.language')}>
            <Select value={settings.language} onChange={handleLanguageChange}>
              <Select.Option value="zh">{t('settings.chinese')}</Select.Option>
              <Select.Option value="en">{t('settings.english')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label={t('settings.theme')}>
            <Select value={settings.theme} onChange={handleThemeChange}>
              <Select.Option value="light">{t('settings.light')}</Select.Option>
              <Select.Option value="dark">{t('settings.dark')}</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {health && (
        <Card title="System Status">
          <Descriptions column={2}>
            <Descriptions.Item label="Status">{health.status}</Descriptions.Item>
            <Descriptions.Item label="Active Sessions">{health.active_sessions}</Descriptions.Item>
            <Descriptions.Item label="Connections">{health.total_connections}</Descriptions.Item>
            <Descriptions.Item label="Providers">{health.total_providers}</Descriptions.Item>
            <Descriptions.Item label="MCP Servers">{health.mcp_servers}</Descriptions.Item>
            <Descriptions.Item label="Skills Loaded">{health.skills_loaded}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  );
}
