import { useState } from 'react'
import { Key, Plus, Trash2, Eye, EyeOff, Check, Copy, Shield } from 'lucide-react'

const PROVIDERS = [
  { id: 'google', label: 'Google Gemini', icon: '🔮', description: 'Gemini Flash & Pro models', envKey: 'GOOGLE_API_KEYS' },
  { id: 'groq', label: 'Groq', icon: '⚡', description: 'Ultra-fast LLaMA inference', envKey: 'GROQ_API_KEYS' },
  { id: 'mistral', label: 'Mistral AI', icon: '🌊', description: 'Mistral Small & Large models', envKey: 'MISTRAL_API_KEYS' },
  { id: 'openrouter', label: 'OpenRouter', icon: '🔀', description: 'Multi-model gateway', envKey: 'OPENROUTER_API_KEYS' },
]

interface KeyEntry {
  id: string
  value: string
  label: string
  active: boolean
}

export default function ApiKeys() {
  const [providerKeys, setProviderKeys] = useState<Record<string, KeyEntry[]>>({
    google: [{ id: '1', value: '', label: 'Primary', active: true }],
    groq: [{ id: '1', value: '', label: 'Primary', active: true }],
    mistral: [{ id: '1', value: '', label: 'Primary', active: true }],
    openrouter: [{ id: '1', value: '', label: 'Primary', active: true }],
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [copied, setCopied] = useState<string | null>(null)

  const addKey = (providerId: string) => {
    setProviderKeys(prev => ({
      ...prev,
      [providerId]: [...prev[providerId], {
        id: String(Date.now()),
        value: '',
        label: `Key ${prev[providerId].length + 1}`,
        active: true,
      }]
    }))
  }

  const removeKey = (providerId: string, keyId: string) => {
    setProviderKeys(prev => ({
      ...prev,
      [providerId]: prev[providerId].filter(k => k.id !== keyId)
    }))
  }

  const updateKey = (providerId: string, keyId: string, value: string) => {
    setProviderKeys(prev => ({
      ...prev,
      [providerId]: prev[providerId].map(k => k.id === keyId ? { ...k, value } : k)
    }))
  }

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setCopied(key)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          API <span className="gradient-text">Key Management</span>
        </h2>
        <p className="text-muted-foreground mt-2">Configure multiple API keys per provider for automatic rotation and failover.</p>
      </div>

      {/* Security notice */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-primary-500/5 border border-primary-500/10">
        <Shield size={18} className="text-primary-400 mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-medium text-primary-300">Multi-Key Rotation</p>
          <p className="text-xs text-muted-foreground mt-1">
            NexusForge automatically rotates through your keys when rate limits are hit. Add multiple keys to maximize throughput.
          </p>
        </div>
      </div>

      {/* Provider sections */}
      <div className="space-y-4">
        {PROVIDERS.map(provider => {
          const keys = providerKeys[provider.id] || []
          const configuredCount = keys.filter(k => k.value.length > 5).length

          return (
            <div key={provider.id} className="glass-card-static overflow-hidden">
              {/* Header */}
              <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{provider.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm">{provider.label}</h3>
                    <p className="text-xs text-muted-foreground">{provider.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {configuredCount > 0 && (
                    <span className="text-xs font-medium text-success bg-success/10 px-2.5 py-1 rounded-full">
                      {configuredCount} key{configuredCount > 1 ? 's' : ''} active
                    </span>
                  )}
                  <button
                    onClick={() => addKey(provider.id)}
                    className="btn-secondary text-xs py-1.5 px-3"
                  >
                    <Plus size={12} /> Add Key
                  </button>
                </div>
              </div>

              {/* Keys */}
              <div className="p-4 space-y-3">
                {keys.map((key, idx) => (
                  <div key={key.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.03]">
                    <div className="w-6 h-6 rounded-md bg-white/[0.04] flex items-center justify-center text-[10px] font-bold text-muted-foreground shrink-0">
                      {idx + 1}
                    </div>
                    <div className="flex-1 relative">
                      <input
                        type={showKeys[`${provider.id}-${key.id}`] ? 'text' : 'password'}
                        value={key.value}
                        onChange={(e) => updateKey(provider.id, key.id, e.target.value)}
                        placeholder={`Enter ${provider.label} API key...`}
                        className="input-field text-xs py-2 pr-20"
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                        <button
                          onClick={() => setShowKeys(prev => ({...prev, [`${provider.id}-${key.id}`]: !prev[`${provider.id}-${key.id}`]}))}
                          className="p-1 text-muted-foreground hover:text-white transition-colors"
                        >
                          {showKeys[`${provider.id}-${key.id}`] ? <EyeOff size={12} /> : <Eye size={12} />}
                        </button>
                        {key.value && (
                          <button
                            onClick={() => copyKey(key.value)}
                            className="p-1 text-muted-foreground hover:text-white transition-colors"
                          >
                            {copied === key.value ? <Check size={12} className="text-success" /> : <Copy size={12} />}
                          </button>
                        )}
                      </div>
                    </div>
                    {keys.length > 1 && (
                      <button
                        onClick={() => removeKey(provider.id, key.id)}
                        className="p-2 text-muted-foreground hover:text-danger transition-colors shrink-0"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
