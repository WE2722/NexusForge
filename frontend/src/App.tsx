import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ProjectCreator from './pages/ProjectCreator';
import ProjectDetail from './pages/ProjectDetail';
import AgentMonitor from './pages/AgentMonitor';
import Settings from './pages/Settings';
import ApiKeys from './pages/ApiKeys';
import TokenDashboard from './pages/TokenDashboard';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="create" element={<ProjectCreator />} />
        <Route path="project/:id" element={<ProjectDetail />} />
        <Route path="agents" element={<AgentMonitor />} />
        <Route path="settings" element={<Settings />} />
        <Route path="keys" element={<ApiKeys />} />
        <Route path="tokens" element={<TokenDashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
