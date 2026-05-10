import { useState, useEffect } from 'react'
import { Plus, Trash2, Eye, EyeOff, Check, Copy, Shield, Loader2, Zap, XCircle } from 'lucide-react'
import axios from 'axios'

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
  testStatus?: 'idle' | 'testing' | 'valid' | 'invalid'
  testError?: string
}

export default function ApiKeys() {
  const [providerKeys, setProviderKeys] = useState<Record<string, KeyEntry[]>>({
    google: [{ id: '1', value: '', label: 'Primary', active: true, testStatus: 'idle' }],
    groq: [{ id: '1', value: '', label: 'Primary', active: true, testStatus: 'idle' }],
    mistral: [{ id: '1', value: '', label: 'Primary', active: true, testStatus: 'idle' }],
    openrouter: [{ id: '1', value: '', label: 'Primary', active: true, testStatus: 'idle' }],
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [copied, setCopied] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Load existing keys on mount
  useEffect(() => {
    loadKeys()
  }, [])

  const loadKeys = async () => {
    try {
      const { data } = await axios.get('/api/keys')
      const loaded: Record<string, KeyEntry[]> = {}
      for (const provider of PROVIDERS) {
        const savedKeys = data[provider.id] || []
        if (savedKeys.length > 0) {
          loaded[provider.id] = savedKeys.map((k: any, i: number) => ({
            id: String(i + 1),
            value: '', // Don't show actual keys, just show masked placeholder
            label: i === 0 ? 'Primary' : `Key ${i + 1}`,
            active: k.active,
            testStatus: 'valid' as const, // Already saved = previously validated
          }))
        } else {
          loaded[provider.id] = [{ id: '1', value: '', label: 'Primary', active: true, testStatus: 'idle' }]
        }
      }
      setProviderKeys(loaded)
    } catch {
      // API may not be ready yet
    }
  }

  const addKey = (providerId: string) => {
    setProviderKeys(prev => ({
      ...prev,
      [providerId]: [...prev[providerId], {
        id: String(Date.now()),
        value: '',
        label: `Key ${prev[providerId].length + 1}`,
        active: true,
        testStatus: 'idle' as const,
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
      [providerId]: prev[providerId].map(k =>
        k.id === keyId ? { ...k, value, testStatus: 'idle' as const } : k
      )
    }))
  }

  const testKey = async (providerId: string, keyId: string) => {
    const key = providerKeys[providerId]?.find(k => k.id === keyId)
    if (!key || !key.value) return

    // Set testing status
    setProviderKeys(prev => ({
      ...prev,
      [providerId]: prev[providerId].map(k =>
        k.id === keyId ? { ...k, testStatus: 'testing' as const } : k
      )
    }))

    try {
      const { data } = await axios.post('/api/keys/test', {
        provider: providerId,
        key: key.value,
      })

      setProviderKeys(prev => ({
        ...prev,
        [providerId]: prev[providerId].map(k =>
          k.id === keyId ? {
            ...k,
            testStatus: data.valid ? 'valid' as const : 'invalid' as const,
            testError: data.valid ? undefined : data.error,
          } : k
        )
      }))
    } catch (e: any) {
      setProviderKeys(prev => ({
        ...prev,
        [providerId]: prev[providerId].map(k =>
          k.id === keyId ? { ...k, testStatus: 'invalid' as const, testError: 'Connection failed' } : k
        )
      }))
    }
  }

  const saveAllKeys = async () => {
    setSaving(true)
    try {
      for (const provider of PROVIDERS) {
        const keys = providerKeys[provider.id]?.filter(k => k.value.trim()) || []
        if (keys.length > 0) {
          await axios.post('/api/keys', {
            provider: provider.id,
            keys: keys.map(k => k.value.trim()),
          })
        }
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('Failed to save keys:', e)
    } finally {
      setSaving(false)
    }
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
          const configuredCount = keys.filter(k => k.value.length > 5 || k.testStatus === 'valid').length

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

                    {/* Test Button */}
                    <button
                      onClick={() => testKey(provider.id, key.id)}
                      disabled={!key.value || key.testStatus === 'testing'}
                      className={`shrink-0 text-xs py-1.5 px-3 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                        key.testStatus === 'valid'
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                          : key.testStatus === 'invalid'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                          : 'bg-white/[0.04] text-muted-foreground hover:text-white border border-white/[0.06] hover:bg-white/[0.06]'
                      } disabled:opacity-30 disabled:cursor-not-allowed`}
                    >
                      {key.testStatus === 'testing' ? (
                        <><Loader2 size={12} className="animate-spin" /> Testing...</>
                      ) : key.testStatus === 'valid' ? (
                        <><Check size={12} /> Valid</>
                      ) : key.testStatus === 'invalid' ? (
                        <><XCircle size={12} /> Invalid</>
                      ) : (
                        <><Zap size={12} /> Test</>
                      )}
                    </button>

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

      {/* Save All */}
      <div className="flex justify-end">
        <button onClick={saveAllKeys} disabled={saving} className="btn-primary px-6">
          {saving ? (
            <><Loader2 size={16} className="animate-spin" /> Saving...</>
          ) : saved ? (
            <><Check size={16} /> Saved!</>
          ) : (
            <>Save All Keys</>
          )}
        </button>
      </div>
    </div>
  )
}
