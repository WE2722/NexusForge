import { useState, useEffect } from 'react'
import { AlertCircle, TrendingUp } from 'lucide-react'
import axios from 'axios'

interface ProviderBudget {
  quota: { tokens_per_minute: number; requests_per_minute: number }
  used: { tokens_minute: number; requests_minute: number }
  remaining: Record<string, number>
  can_use: boolean
}

const PROVIDER_META: Record<string, { icon: string; label: string }> = {
  google: { icon: '🔮', label: 'Gemini' },
  groq: { icon: '⚡', label: 'Groq' },
  mistral: { icon: '🌊', label: 'Mistral' },
  openrouter: { icon: '🔀', label: 'OpenRouter' },
}

export default function TokenMonitor() {
  const [budget, setBudget] = useState<Record<string, ProviderBudget>>({})

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await axios.get('/api/budget')
        setBudget(data)
      } catch (e) {}
    }
    fetch()
    const interval = setInterval(fetch, 5000)
    return () => clearInterval(interval)
  }, [])

  const providers = Object.entries(budget)
  if (providers.length === 0) return null

  return (
    <div className="glass-card-static p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <TrendingUp size={12} /> Token Usage
        </h4>
      </div>

      {providers.map(([key, data]) => {
        const meta = PROVIDER_META[key]
        if (!meta) return null
        const quota = data.quota?.tokens_per_minute || 0
        const used = data.used?.tokens_minute || 0
        const pct = quota > 0 ? Math.min(100, (used / quota) * 100) : 0
        const isWarning = pct > 80
        const isCritical = pct > 95

        return (
          <div key={key} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium flex items-center gap-1.5">
                {meta.icon} {meta.label}
              </span>
              <span className={`text-[10px] font-bold ${isCritical ? 'text-danger' : isWarning ? 'text-warning' : 'text-muted-foreground'}`}>
                {pct.toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isCritical ? 'bg-danger' : isWarning ? 'bg-warning' : 'bg-primary-500'
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            {isCritical && (
              <p className="text-[10px] text-danger flex items-center gap-1">
                <AlertCircle size={10} /> Rate limit imminent
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
