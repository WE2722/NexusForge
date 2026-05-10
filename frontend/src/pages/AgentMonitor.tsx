import { Activity, ShieldCheck, Database, Cpu, Layout, Code2, Bug, Zap } from 'lucide-react'
import { useAgents } from '../hooks/useAgents'

const AGENT_COLORS: Record<string, { gradient: string; text: string; bg: string }> = {
  architecture: { gradient: 'from-purple-500 to-violet-600', text: 'text-purple-400', bg: 'bg-purple-500/10' },
  backend: { gradient: 'from-emerald-500 to-green-600', text: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  frontend: { gradient: 'from-blue-500 to-cyan-600', text: 'text-blue-400', bg: 'bg-blue-500/10' },
  database: { gradient: 'from-amber-500 to-yellow-600', text: 'text-amber-400', bg: 'bg-amber-500/10' },
  debugger: { gradient: 'from-red-500 to-rose-600', text: 'text-red-400', bg: 'bg-red-500/10' },
  review: { gradient: 'from-teal-500 to-cyan-600', text: 'text-teal-400', bg: 'bg-teal-500/10' },
}

const AGENT_ICONS: Record<string, React.ReactNode> = {
  architecture: <Cpu size={22} />,
  backend: <Code2 size={22} />,
  frontend: <Layout size={22} />,
  database: <Database size={22} />,
  debugger: <Bug size={22} />,
  review: <ShieldCheck size={22} />,
}

const AGENT_DESCRIPTIONS: Record<string, string> = {
  architecture: 'Designs system architecture, API contracts, and data models for your project.',
  backend: 'Generates production-ready Python/FastAPI backend code with proper endpoints.',
  frontend: 'Creates beautiful React/TypeScript UI components with modern design patterns.',
  database: 'Designs database schemas, indexes, and migration scripts for optimal performance.',
  debugger: 'Analyzes errors, diagnoses root causes, and generates corrected code automatically.',
  review: 'Reviews all generated code for correctness, security, and integration consistency.',
}

/* ── Connection Lines (SVG) ── */
function AgentNetwork() {
  return (
    <div className="relative w-full h-20 mb-4">
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 800 80" preserveAspectRatio="none">
        <defs>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="rgba(99, 102, 241, 0.3)" />
            <stop offset="50%" stopColor="rgba(139, 92, 246, 0.2)" />
            <stop offset="100%" stopColor="rgba(99, 102, 241, 0.3)" />
          </linearGradient>
        </defs>
        {/* Horizontal connection */}
        <path d="M 0 40 Q 400 10 800 40" stroke="url(#lineGrad)" strokeWidth="1" fill="none" strokeDasharray="4 4">
          <animate attributeName="stroke-dashoffset" from="0" to="-8" dur="1s" repeatCount="indefinite" />
        </path>
        <path d="M 0 40 Q 400 70 800 40" stroke="url(#lineGrad)" strokeWidth="1" fill="none" strokeDasharray="4 4">
          <animate attributeName="stroke-dashoffset" from="0" to="-8" dur="1.5s" repeatCount="indefinite" />
        </path>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <Zap size={14} className="text-accent" />
          <span className="text-xs font-medium text-muted-foreground">Multi-Agent Orchestration Pipeline</span>
        </div>
      </div>
    </div>
  )
}

export default function AgentMonitor() {
  const { agents, loading } = useAgents()

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Agent <span className="gradient-text">Network</span>
        </h2>
        <p className="text-muted-foreground mt-2">Monitor the status and capabilities of your specialized AI agents.</p>
      </div>

      <AgentNetwork />

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-56 rounded-2xl bg-white/[0.02] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 stagger-children">
          {agents.map(agent => {
            const colors = AGENT_COLORS[agent.agent_type] || AGENT_COLORS.backend
            const icon = AGENT_ICONS[agent.agent_type]
            const desc = AGENT_DESCRIPTIONS[agent.agent_type] || ''

            return (
              <div key={agent.name} className="glass-card p-6 group relative overflow-hidden">
                {/* Glow effect */}
                <div className={`absolute top-0 right-0 w-28 h-28 bg-gradient-to-bl ${colors.gradient} rounded-full blur-3xl opacity-10 group-hover:opacity-20 transition-opacity -translate-y-6 translate-x-6`} />

                <div className="relative">
                  {/* Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div className={`p-3 rounded-xl ${colors.bg} ${colors.text}`}>
                      {icon}
                    </div>
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 border border-success/20">
                      <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                      <span className="text-[10px] font-semibold text-success uppercase tracking-wider">Online</span>
                    </div>
                  </div>

                  {/* Info */}
                  <h3 className="text-base font-bold capitalize mb-1">{agent.name} Agent</h3>
                  <p className="text-xs text-muted-foreground mb-4 leading-relaxed">{desc}</p>

                  {/* Expertise tags */}
                  <div className="mb-4">
                    <p className="text-[10px] text-muted-foreground mb-2 uppercase tracking-wider font-bold">Expertise</p>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.expertise.map(e => (
                        <span key={e} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-white/[0.04] border border-white/[0.06] text-gray-400">{e}</span>
                      ))}
                    </div>
                  </div>

                  {/* Providers */}
                  <div>
                    <p className="text-[10px] text-muted-foreground mb-2 uppercase tracking-wider font-bold">Preferred Models</p>
                    <div className="flex gap-2">
                      {agent.preferred_providers.map(p => (
                        <span key={p} className={`text-[10px] font-semibold capitalize ${colors.text}`}>{p}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
