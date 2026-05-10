import { useState, useEffect } from 'react'
import { Save, Key, Palette, BarChart3, Eye, EyeOff, Check, AlertCircle } from 'lucide-react'
import axios from 'axios'

const PROVIDERS = [
  { id: 'google', label: 'Google Gemini', icon: '🔮', color: 'text-blue-400' },
  { id: 'groq', label: 'Groq', icon: '⚡', color: 'text-orange-400' },
  { id: 'mistral', label: 'Mistral AI', icon: '🌊', color: 'text-cyan-400' },
  { id: 'openrouter', label: 'OpenRouter', icon: '🔀', color: 'text-purple-400' },
]

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'keys' | 'preferences' | 'budget'>('keys')
  const [keys, setKeys] = useState<Record<string, string>>({
    google: '', groq: '', mistral: '', openrouter: ''
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [saved, setSaved] = useState(false)
  const [budget, setBudget] = useState<Record<string, any>>({})

  useEffect(() => {
    fetchBudget()
  }, [])

  const fetchBudget = async () => {
    try {
      const { data } = await axios.get('/api/budget')
      setBudget(data)
    } catch (e) {
      // Budget endpoint may not be available yet
    }
  }

  const handleSave = async () => {
    try {
      await axios.post('/api/keys/save-all', keys)
      // Save preferences to localStorage
      localStorage.setItem('nexusforge_settings', JSON.stringify(keys))
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('Failed to save settings:', e)
    }
  }

  // Load saved keys from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('nexusforge_settings')
    if (saved) {
      try {
        setKeys(JSON.parse(saved))
      } catch {}
    }
  }, [])

  const tabs = [
    { id: 'keys' as const, label: 'API Keys', icon: Key },
    { id: 'preferences' as const, label: 'Preferences', icon: Palette },
    { id: 'budget' as const, label: 'Token Budget', icon: BarChart3 },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          <span className="gradient-text">Settings</span>
        </h2>
        <p className="text-muted-foreground mt-2">Manage your API keys, preferences, and token budgets.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-white/[0.02] rounded-xl w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              activeTab === tab.id
                ? 'bg-white/[0.06] text-white'
                : 'text-muted-foreground hover:text-white'
            }`}
          >
            <tab.icon size={14} /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'keys' && (
        <div className="glass-card-static p-6 space-y-6 animate-fade-in">
          <div className="flex items-center gap-2">
            <Key size={18} className="text-accent" />
            <h3 className="text-lg font-semibold">API Keys</h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Configure your LLM provider API keys. Keys are stored locally and never sent to third parties.
          </p>

          <div className="space-y-4">
            {PROVIDERS.map(provider => (
              <div key={provider.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span>{provider.icon}</span>
                    <label className="text-sm font-medium">{provider.label}</label>
                  </div>
                  {keys[provider.id] && (
                    <div className="flex items-center gap-1 text-xs text-success">
                      <Check size={12} /> Configured
                    </div>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showKeys[provider.id] ? 'text' : 'password'}
                    value={keys[provider.id]}
                    onChange={(e) => setKeys({...keys, [provider.id]: e.target.value})}
                    placeholder={`Enter ${provider.label} API key...`}
                    className="input-field pr-10"
                  />
                  <button
                    onClick={() => setShowKeys({...showKeys, [provider.id]: !showKeys[provider.id]})}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                  >
                    {showKeys[provider.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <button onClick={handleSave} className="btn-primary">
              {saved ? <><Check size={16} /> Saved!</> : <><Save size={16} /> Save Keys</>}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'preferences' && (
        <div className="glass-card-static p-6 space-y-6 animate-fade-in">
          <div className="flex items-center gap-2">
            <Palette size={18} className="text-accent" />
            <h3 className="text-lg font-semibold">Preferences</h3>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <label className="text-sm font-medium block mb-2">Default LLM Provider</label>
              <select className="input-field" defaultValue="google">
                {PROVIDERS.map(p => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </div>

            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <label className="text-sm font-medium block mb-2">Max Tokens Per Project</label>
              <input type="number" defaultValue={50000} className="input-field" />
            </div>

            <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-between">
              <div>
                <label className="text-sm font-medium block">Auto-Debug Failed Tasks</label>
                <p className="text-xs text-muted-foreground mt-0.5">Automatically retry failed tasks with the debugger agent</p>
              </div>
              <div className="w-10 h-6 bg-primary-500 rounded-full relative cursor-pointer">
                <div className="absolute right-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-all" />
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'budget' && (
        <div className="glass-card-static p-6 space-y-6 animate-fade-in">
          <div className="flex items-center gap-2">
            <BarChart3 size={18} className="text-accent" />
            <h3 className="text-lg font-semibold">Token Budget</h3>
          </div>

          <div className="space-y-4">
            {PROVIDERS.map(provider => {
              const data = budget[provider.id]
              const used = data?.used?.tokens_minute || 0
              const quota = data?.quota?.tokens_per_minute || 100000
              const pct = quota > 0 ? Math.min(100, (used / quota) * 100) : 0

              return (
                <div key={provider.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span>{provider.icon}</span>
                      <span className="text-sm font-medium">{provider.label}</span>
                    </div>
                    <span className={`text-xs font-medium ${pct > 80 ? 'text-danger' : pct > 50 ? 'text-warning' : 'text-success'}`}>
                      {pct.toFixed(0)}% used
                    </span>
                  </div>
                  <div className="w-full h-2 bg-white/[0.04] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        pct > 80 ? 'bg-danger' : pct > 50 ? 'bg-warning' : 'bg-success'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
                    <span>{used.toLocaleString()} tokens used</span>
                    <span>{quota.toLocaleString()} TPM limit</span>
                  </div>
                  {pct > 80 && (
                    <div className="mt-2 flex items-center gap-1 text-xs text-danger">
                      <AlertCircle size={12} /> Approaching rate limit
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
