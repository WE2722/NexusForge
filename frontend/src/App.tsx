import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ProjectCreator from './pages/ProjectCreator';
import ProjectDetail from './pages/ProjectDetail';
import AgentMonitor from './pages/AgentMonitor';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="create" element={<ProjectCreator />} />
        <Route path="project/:id" element={<ProjectDetail />} />
        <Route path="agents" element={<AgentMonitor />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
