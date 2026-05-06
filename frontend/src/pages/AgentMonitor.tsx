import { Activity, ShieldCheck, Database, Cpu, Layout, Code2 } from 'lucide-react'
import { useAgents } from '../hooks/useAgents'

export default function AgentMonitor() {
  const { agents, loading } = useAgents()

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'frontend': return <Layout className="text-blue-500" />
      case 'backend': return <Code2 className="text-green-500" />
      case 'database': return <Database className="text-yellow-500" />
      case 'architecture': return <Cpu className="text-purple-500" />
      case 'debugger': return <Activity className="text-red-500" />
      case 'review': return <ShieldCheck className="text-teal-500" />
      default: return <Activity />
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Agent Network</h2>
        <p className="text-muted-foreground mt-1">Monitor the status and capabilities of your specialized AI agents.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1,2,3,4,5,6].map(i => <div key={i} className="h-48 bg-card rounded-lg border border-border"></div>)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map(agent => (
            <div key={agent.name} className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-muted rounded-lg">
                  {getAgentIcon(agent.agent_type)}
                </div>
                <span className="flex items-center gap-1 text-xs font-medium text-green-500 bg-green-500/10 px-2 py-1 rounded">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  Ready
                </span>
              </div>
              <h3 className="text-lg font-bold capitalize">{agent.name} Agent</h3>
              <p className="text-sm text-muted-foreground mb-4">{agent.role}</p>
              
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wider">Expertise</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.expertise.slice(0, 3).map(e => (
                      <span key={e} className="text-xs bg-muted px-2 py-1 rounded">{e}</span>
                    ))}
                    {agent.expertise.length > 3 && <span className="text-xs bg-muted px-2 py-1 rounded">+{agent.expertise.length - 3}</span>}
                  </div>
                </div>
                <div>
                   <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wider">Preferred Models</p>
                   <div className="flex gap-2">
                     {agent.preferred_providers.map(p => (
                       <span key={p} className="text-xs capitalize font-medium">{p}</span>
                     ))}
                   </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
