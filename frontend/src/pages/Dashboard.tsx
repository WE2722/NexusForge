import { Link } from 'react-router-dom'
import { PlusCircle, Code, Layers, Zap } from 'lucide-react'
import { useProjects } from '../hooks/useProject'
import StatsCard from '../components/StatsCard'
import TemplateGallery from '../components/TemplateGallery'
import AgentChat from '../components/AgentChat'

export default function Dashboard() {
  const { projects, loading } = useProjects()

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground mt-1">Overview of your NexusForge projects</p>
        </div>
        <Link to="/create" className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md flex items-center gap-2 transition-colors font-medium">
          <PlusCircle size={18} /> New Project
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard title="Total Projects" value={projects.length} icon={<Layers />} />
        <StatsCard title="Active Agents" value="6" icon={<Zap />} />
        <StatsCard title="Tokens Saved" value="124k" icon={<Code />} trend="+12% this week" />
      </div>

      <div>
        <h3 className="text-xl font-bold mb-4">Quick Start Templates</h3>
        <TemplateGallery onSelect={(t) => console.log(t)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Recent Projects</h3>
          {loading ? (
            <div className="animate-pulse flex flex-col gap-4">
              {[1,2,3].map(i => <div key={i} className="h-16 bg-muted/50 rounded-lg w-full"></div>)}
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No projects found. Create your first project to get started.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {projects.map(p => (
                <div key={p.id} className="py-4 flex justify-between items-center hover:bg-muted/20 px-2 rounded transition-colors -mx-2">
                  <div>
                    <Link to={`/project/${p.id}`} className="font-semibold hover:text-primary transition-colors">{p.title}</Link>
                    <p className="text-sm text-muted-foreground mt-1">Status: <span className="capitalize">{p.status}</span> • {p.completed_tasks}/{p.task_count} Tasks</p>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div>
          <AgentChat messages={[
            { agent: 'System', text: 'NexusForge online.' },
            { agent: 'Architecture', text: 'Analyzed recent project patterns.' },
            { agent: 'Review', text: 'Ready for code inspection.' }
          ]} />
        </div>
      </div>
    </div>
  )
}
