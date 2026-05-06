import { useState } from 'react'
import { Save, Key } from 'lucide-react'

export default function Settings() {
  const [keys, setKeys] = useState({
    google: '',
    groq: '',
    mistral: '',
    openrouter: ''
  })

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground mt-1">Manage your API keys and preferences.</p>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Key size={20} className="text-primary" />
          <h3 className="text-xl font-semibold">API Keys</h3>
        </div>
        
        <div className="space-y-4">
          {Object.entries(keys).map(([provider, val]) => (
            <div key={provider}>
              <label className="block text-sm font-medium mb-1 capitalize">{provider} API Key</label>
              <input 
                type="password"
                value={val}
                onChange={(e) => setKeys({...keys, [provider]: e.target.value})}
                placeholder={`sk-...`}
                className="w-full p-2 bg-background border border-border rounded focus:outline-none focus:border-primary"
              />
            </div>
          ))}
        </div>

        <div className="pt-4 flex justify-end">
          <button className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md flex items-center gap-2 transition-colors font-medium">
            <Save size={18} /> Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}
