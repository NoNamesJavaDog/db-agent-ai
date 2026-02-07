import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/layout/AppLayout';
import ChatPage from './pages/ChatPage';
import ConnectionsPage from './pages/ConnectionsPage';
import ProvidersPage from './pages/ProvidersPage';
import SessionsPage from './pages/SessionsPage';
import McpPage from './pages/McpPage';
import SkillsPage from './pages/SkillsPage';
import MigrationPage from './pages/MigrationPage';
import SettingsPage from './pages/SettingsPage';
import './i18n';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<Navigate to="/chat" replace />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="connections" element={<ConnectionsPage />} />
              <Route path="providers" element={<ProvidersPage />} />
              <Route path="sessions" element={<SessionsPage />} />
              <Route path="mcp" element={<McpPage />} />
              <Route path="skills" element={<SkillsPage />} />
              <Route path="migration" element={<MigrationPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;
