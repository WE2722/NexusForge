import { useState, useEffect } from 'react'
import { TrendingUp, AlertCircle, Activity, Zap, Server, Bot, BarChart3, RefreshCw } from 'lucide-react'
import axios from 'axios'

interface ProviderStats {
  used: number
  total: number
  percentage: number
  remaining_pct: number
  can_use: boolean
  requests_today: number
}

interface AgentStats {
  calls: number
  tokens: number
}

interface TokenData {
  providers: Record<string, ProviderStats>
  agents: Record<string, AgentStats>
  total_projects: number
  total_tokens_used: number
}

const PROVIDER_META: Record<string, { icon: string; label: string; color: string }> = {
  google: { icon: '🔮', label: 'Google Gemini', color: '#818cf8' },
  groq: { icon: '⚡', label: 'Groq', color: '#f59e0b' },
  mistral: { icon: '🌊', label: 'Mistral AI', color: '#06b6d4' },
  openrouter: { icon: '🔀', label: 'OpenRouter', color: '#a78bfa' },
}

const AGENT_COLORS: Record<string, string> = {
  frontend_agent: '#818cf8',
  backend_agent: '#34d399',
  database_agent: '#fbbf24',
  architecture_agent: '#f472b6',
  debugger_agent: '#ef4444',
  review_agent: '#a78bfa',
  frontend: '#818cf8',
  backend: '#34d399',
  database: '#fbbf24',
  architecture: '#f472b6',
  debugger: '#ef4444',
  review: '#a78bfa',
}

function getBarColor(pct: number): string {
  const remaining = 100 - pct
  if (remaining > 50) return 'from-emerald-500 to-green-400'
  if (remaining > 20) return 'from-amber-500 to-yellow-400'
  return 'from-red-500 to-rose-400'
}

function getBadgeColor(pct: number): string {
  const remaining = 100 - pct
  if (remaining > 50) return 'text-green-400 bg-green-500/10 border-green-500/20'
  if (remaining > 20) return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  return 'text-red-400 bg-red-500/10 border-red-500/20'
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

export default function TokenDashboard() {
  const [data, setData] = useState<TokenData | null>(null)
  const [budgetData, setBudgetData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const fetchData = async () => {
    try {
      const [tokenResp, budgetResp] = await Promise.all([
        axios.get('/api/tokens'),
        axios.get('/api/budget'),
      ])
      setData(tokenResp.data)
      setBudgetData(budgetResp.data)
      setLastUpdated(new Date())
    } catch (e) {
      console.error('Failed to fetch token data:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const criticalProviders = data
    ? Object.entries(data.providers).filter(([, p]) => p.remaining_pct < 20)
    : []

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-primary-500/20 border-t-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading token usage data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Token <span className="gradient-text">Usage</span>
          </h2>
          <p className="text-muted-foreground mt-1">Real-time monitoring across all LLM providers</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
          <button onClick={fetchData} className="btn-secondary text-sm py-2 px-3">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Alert Banner */}
      {criticalProviders.length > 0 && (
        <div className="px-5 py-4 rounded-xl bg-red-500/5 border border-red-500/15 flex items-start gap-3 animate-slide-up">
          <AlertCircle size={18} className="text-red-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-400">Rate Limit Warning</p>
            <p className="text-xs text-red-400/70 mt-0.5">
              {criticalProviders.map(([name]) => PROVIDER_META[name]?.label || name).join(', ')}
              {' '}— less than 20% capacity remaining
            </p>
          </div>
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-primary-500/15 to-transparent rounded-full blur-2xl -translate-y-6 translate-x-6" />
          <div className="relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Total Tokens Used</span>
              <Zap size={16} className="text-primary-400" />
            </div>
            <p className="text-2xl font-bold">{formatNumber(data?.total_tokens_used || 0)}</p>
          </div>
        </div>

        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-green-500/15 to-transparent rounded-full blur-2xl -translate-y-6 translate-x-6" />
          <div className="relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Total Projects</span>
              <BarChart3 size={16} className="text-green-400" />
            </div>
            <p className="text-2xl font-bold">{data?.total_projects || 0}</p>
          </div>
        </div>

        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-amber-500/15 to-transparent rounded-full blur-2xl -translate-y-6 translate-x-6" />
          <div className="relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Active Providers</span>
              <Server size={16} className="text-amber-400" />
            </div>
            <p className="text-2xl font-bold">
              {data ? Object.values(data.providers).filter(p => p.can_use).length : 0}
              <span className="text-sm text-muted-foreground font-normal"> / {data ? Object.keys(data.providers).length : 0}</span>
            </p>
          </div>
        </div>

        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-purple-500/15 to-transparent rounded-full blur-2xl -translate-y-6 translate-x-6" />
          <div className="relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Active Agents</span>
              <Bot size={16} className="text-purple-400" />
            </div>
            <p className="text-2xl font-bold">{data ? Object.keys(data.agents).length : 0}</p>
          </div>
        </div>
      </div>

      {/* Provider Usage */}
      <div className="glass-card-static p-6">
        <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
          <TrendingUp size={16} className="text-accent" /> Provider Usage
        </h3>
        <div className="space-y-5">
          {data && Object.entries(data.providers).map(([key, provider]) => {
            const meta = PROVIDER_META[key]
            if (!meta) return null
            return (
              <div key={key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{meta.icon}</span>
                    <div>
                      <span className="text-sm font-medium">{meta.label}</span>
                      <p className="text-[10px] text-muted-foreground">
                        {formatNumber(provider.used)} / {formatNumber(provider.total)} tokens
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {provider.requests_today} req today
                    </span>
                    <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border ${getBadgeColor(provider.percentage)}`}>
                      {provider.remaining_pct.toFixed(0)}% left
                    </span>
                  </div>
                </div>
                <div className="w-full h-2.5 bg-white/[0.04] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 bg-gradient-to-r ${getBarColor(provider.percentage)}`}
                    style={{ width: `${Math.min(100, provider.percentage)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Agent Usage */}
      <div className="glass-card-static p-6">
        <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
          <Activity size={16} className="text-accent" /> Agent Activity
        </h3>
        {data && Object.keys(data.agents).length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(data.agents).map(([name, stats]) => (
              <div key={name} className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{
                    backgroundColor: `${AGENT_COLORS[name] || '#6366f1'}15`,
                    border: `1px solid ${AGENT_COLORS[name] || '#6366f1'}30`,
                  }}
                >
                  <Bot size={18} style={{ color: AGENT_COLORS[name] || '#6366f1' }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium capitalize truncate">{name.replace('_', ' ')}</p>
                  <p className="text-xs text-muted-foreground">
                    {stats.calls} calls • {formatNumber(stats.tokens)} tokens
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <Bot size={32} className="mx-auto mb-3 text-muted-foreground opacity-40" />
            <p className="text-sm text-muted-foreground">No agent activity yet. Create a project to see agent usage.</p>
          </div>
        )}
      </div>

      {/* Budget Details (from /api/budget) */}
      {budgetData && (
        <div className="glass-card-static p-6">
          <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
            <Server size={16} className="text-accent" /> Rate Limit Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(budgetData).map(([key, data]: [string, any]) => {
              const meta = PROVIDER_META[key]
              if (!meta || !data) return null
              return (
                <div key={key} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center gap-2 mb-3">
                    <span>{meta.icon}</span>
                    <span className="text-sm font-medium">{meta.label}</span>
                    <span className={`ml-auto w-2 h-2 rounded-full ${data.can_use ? 'bg-green-400' : 'bg-red-500'}`} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Tokens/min</span>
                      <p className="font-medium">{formatNumber(data.used?.tokens_minute || 0)} / {formatNumber(data.quota?.tokens_per_minute || 0)}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Requests/min</span>
                      <p className="font-medium">{data.used?.requests_minute || 0} / {data.quota?.requests_per_minute || 0}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Requests/day</span>
                      <p className="font-medium">{data.used?.requests_day || 0} / {data.quota?.requests_per_day || 0}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Status</span>
                      <p className={`font-medium ${data.can_use ? 'text-green-400' : 'text-red-400'}`}>
                        {data.can_use ? '✅ Available' : '❌ Rate Limited'}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
