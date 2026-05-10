import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { PlusCircle, Layers, Zap, Code, TrendingUp, ArrowRight } from 'lucide-react'
import { useProjects } from '../hooks/useProject'

/* ── Animated Counter Hook ── */
function useCounter(target: number, duration = 1500) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (target === 0) return
    let start = 0
    const step = Math.max(1, Math.ceil(target / (duration / 16)))
    const timer = setInterval(() => {
      start += step
      if (start >= target) {
        setCount(target)
        clearInterval(timer)
      } else {
        setCount(start)
      }
    }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return count
}

/* ── Particle Canvas ── */
function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animId: number
    const particles: { x: number; y: number; vx: number; vy: number; r: number; o: number }[] = []
    const resize = () => { canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight }
    resize()
    window.addEventListener('resize', resize)

    for (let i = 0; i < 40; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
        o: Math.random() * 0.3 + 0.1,
      })
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(139, 92, 246, ${p.o})`
        ctx.fill()
      })
      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
      animId = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize) }
  }, [])
  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
}

/* ── Stats Card ── */
function StatsCard({ title, value, icon, trend, color = 'primary' }: {
  title: string; value: number | string; icon: React.ReactNode; trend?: string; color?: string
}) {
  const numValue = typeof value === 'number' ? value : parseInt(value) || 0
  const displayValue = typeof value === 'number' ? useCounter(numValue) : value

  const colorMap: Record<string, string> = {
    primary: 'from-primary-500/20 to-accent/10',
    green: 'from-success/20 to-emerald-500/10',
    amber: 'from-warning/20 to-amber-500/10',
  }

  return (
    <div className="glass-card p-6 relative overflow-hidden group">
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl ${colorMap[color] || colorMap.primary} rounded-full blur-2xl opacity-50 -translate-y-8 translate-x-8 group-hover:opacity-80 transition-opacity`} />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <span className="text-muted-foreground text-sm font-medium">{title}</span>
          <div className="p-2 rounded-xl bg-white/[0.04]">{icon}</div>
        </div>
        <p className="text-3xl font-bold tracking-tight">{displayValue}</p>
        {trend && (
          <p className="text-xs text-success flex items-center gap-1 mt-2">
            <TrendingUp size={12} /> {trend}
          </p>
        )}
      </div>
    </div>
  )
}

/* ── Template Card ── */
function TemplateCard({ title, desc, icon }: { title: string; desc: string; icon: string }) {
  return (
    <Link to={`/create?template=${encodeURIComponent(title)}`} className="glass-card p-5 cursor-pointer group">
      <div className="text-2xl mb-3">{icon}</div>
      <h4 className="font-semibold text-sm mb-1 group-hover:text-primary-400 transition-colors">{title}</h4>
      <p className="text-xs text-muted-foreground">{desc}</p>
    </Link>
  )
}

/* ── Main Dashboard ── */
export default function Dashboard() {
  const { projects, loading } = useProjects()

  const completedCount = projects.filter(p => p.status === 'completed').length
  const activeCount = projects.filter(p => p.status === 'executing').length

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Section */}
      <div className="relative rounded-2xl overflow-hidden glass-card-static p-8 min-h-[180px] flex items-center">
        <ParticleBackground />
        <div className="relative z-10 flex justify-between items-center w-full">
          <div>
            <h2 className="text-4xl font-bold tracking-tight mb-2">
              Welcome to <span className="gradient-text">NexusForge</span>
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Your AI-powered multi-agent development platform. Describe what you want to build and watch your team of specialized agents bring it to life.
            </p>
          </div>
          <Link to="/create" className="btn-primary text-base px-8 py-3.5 shrink-0">
            <PlusCircle size={20} /> New Project
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 stagger-children">
        <StatsCard title="Total Projects" value={projects.length} icon={<Layers size={18} className="text-primary-400" />} color="primary" />
        <StatsCard title="Completed" value={completedCount} icon={<Zap size={18} className="text-success" />} trend={completedCount > 0 ? "All systems go" : undefined} color="green" />
        <StatsCard title="Active Agents" value={6} icon={<Code size={18} className="text-warning" />} color="amber" />
      </div>

      {/* Quick Start Templates */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap size={16} className="text-accent" /> Quick Start Templates
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children">
          <TemplateCard icon="✅" title="Todo App" desc="Task management with CRUD operations" />
          <TemplateCard icon="🌤" title="Weather Dashboard" desc="Real-time weather with API integration" />
          <TemplateCard icon="📝" title="Blog Platform" desc="Full blog with posts and comments" />
          <TemplateCard icon="💬" title="Chat App" desc="Real-time messaging with WebSockets" />
        </div>
      </div>

      {/* Recent Projects */}
      <div className="glass-card-static p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold">Recent Projects</h3>
          <Link to="/create" className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1 transition-colors">
            View all <ArrowRight size={14} />
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 rounded-xl bg-white/[0.02] animate-pulse" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/[0.03] flex items-center justify-center">
              <Layers size={24} className="text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-4">No projects yet. Create your first project to get started.</p>
            <Link to="/create" className="btn-primary">
              <PlusCircle size={16} /> Create Project
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {projects.slice(0, 5).map((p, i) => (
              <Link
                key={p.id}
                to={`/project/${p.id}`}
                className="flex items-center justify-between p-4 rounded-xl hover:bg-white/[0.03] transition-all group"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent/10 flex items-center justify-center text-sm font-bold text-primary-400">
                    {p.title?.charAt(0) || '#'}
                  </div>
                  <div>
                    <p className="font-medium text-sm group-hover:text-primary-400 transition-colors">{p.title || 'Untitled'}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {p.completed_tasks}/{p.task_count} tasks • {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`status-badge ${
                  p.status === 'completed' ? 'status-completed' :
                  p.status === 'executing' ? 'status-executing' :
                  p.status === 'failed' ? 'status-failed' : 'status-pending'
                }`}>
                  {p.status}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
