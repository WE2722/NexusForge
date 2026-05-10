import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Send, Sparkles, ArrowLeft, ArrowRight, Check, Cpu, Code, Layout, Database } from 'lucide-react'
import { useProjects } from '../hooks/useProject'

const STEPS = ['Describe', 'Configure', 'Review', 'Launch']

const TEMPLATES: Record<string, string> = {
  'Todo App': 'Build a todo application with the ability to add, complete, and delete tasks. Include filtering by status (all, active, completed). Modern dark UI.',
  'Weather Dashboard': 'Build a weather dashboard that fetches real-time weather data and displays current conditions with a 5-day forecast. Include city search. Beautiful charts and cards.',
  'Blog Platform': 'Build a blog platform with posts listing, individual post view, create/edit posts, and a comments section. Clean, minimal design with dark mode.',
  'Chat App': 'Build a real-time chat application with multiple chat rooms, message sending, and user presence indicators. Modern messaging UI with dark theme.',
}

const TECH_OPTIONS = [
  { id: 'fastapi', label: 'FastAPI', icon: '⚡', category: 'backend' },
  { id: 'react', label: 'React', icon: '⚛️', category: 'frontend' },
  { id: 'typescript', label: 'TypeScript', icon: '📘', category: 'frontend' },
  { id: 'mongodb', label: 'MongoDB', icon: '🍃', category: 'database' },
  { id: 'tailwind', label: 'Tailwind CSS', icon: '🎨', category: 'frontend' },
  { id: 'websocket', label: 'WebSocket', icon: '🔌', category: 'backend' },
]

export default function ProjectCreator() {
  const [searchParams] = useSearchParams()
  const templateName = searchParams.get('template')
  const initialPrompt = templateName ? TEMPLATES[templateName] || '' : ''

  const [step, setStep] = useState(0)
  const [prompt, setPrompt] = useState(initialPrompt)
  const [selectedTech, setSelectedTech] = useState<string[]>(['fastapi', 'react', 'typescript'])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { createProject } = useProjects()
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!prompt.trim() || isSubmitting) return
    setIsSubmitting(true)
    try {
      const techStr = selectedTech.length > 0 ? `\nTech stack: ${selectedTech.join(', ')}` : ''
      const project = await createProject(prompt + techStr)
      navigate(`/project/${project.id}`)
    } catch (err) {
      console.error(err)
      setIsSubmitting(false)
    }
  }

  const canProceed = () => {
    if (step === 0) return prompt.trim().length >= 10
    return true
  }

  const nextStep = () => {
    if (step === STEPS.length - 1) {
      handleSubmit()
    } else {
      setStep(s => Math.min(s + 1, STEPS.length - 1))
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Create <span className="gradient-text">New Project</span>
        </h2>
        <p className="text-muted-foreground mt-2">Describe what you want to build and our AI agents will handle the rest.</p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <button
              onClick={() => i < step && setStep(i)}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shrink-0 ${
                i < step ? 'bg-success text-white' :
                i === step ? 'bg-gradient-to-br from-primary-500 to-accent text-white shadow-lg shadow-primary-500/30' :
                'bg-white/[0.04] text-muted-foreground'
              }`}
            >
              {i < step ? <Check size={14} /> : i + 1}
            </button>
            <span className={`text-xs font-medium hidden sm:block ${i === step ? 'text-white' : 'text-muted-foreground'}`}>{s}</span>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-px ${i < step ? 'bg-success' : 'bg-white/[0.06]'}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="glass-card-static p-8 min-h-[320px]">
        {step === 0 && (
          <div className="space-y-5 animate-fade-in">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={18} className="text-accent" />
              <h3 className="font-semibold">Describe Your Project</h3>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Build a real-time chat application with React, FastAPI, and WebSockets. Include user authentication, multiple chat rooms, and message history..."
              className="input-field h-48 resize-none"
              autoFocus
            />
            <div className="flex flex-wrap gap-2">
              {Object.keys(TEMPLATES).map(name => (
                <button
                  key={name}
                  onClick={() => setPrompt(TEMPLATES[name])}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/[0.04] hover:bg-white/[0.08] text-muted-foreground hover:text-white transition-all border border-white/[0.04]"
                >
                  {name}
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-5 animate-fade-in">
            <div className="flex items-center gap-2 mb-2">
              <Cpu size={18} className="text-accent" />
              <h3 className="font-semibold">Configure Tech Stack</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {TECH_OPTIONS.map(tech => {
                const selected = selectedTech.includes(tech.id)
                return (
                  <button
                    key={tech.id}
                    onClick={() => setSelectedTech(prev =>
                      selected ? prev.filter(t => t !== tech.id) : [...prev, tech.id]
                    )}
                    className={`p-4 rounded-xl text-left transition-all border ${
                      selected
                        ? 'bg-primary-500/10 border-primary-500/30 text-white'
                        : 'bg-white/[0.02] border-white/[0.04] text-muted-foreground hover:border-white/[0.1]'
                    }`}
                  >
                    <div className="text-lg mb-1">{tech.icon}</div>
                    <p className="text-sm font-medium">{tech.label}</p>
                    <p className="text-xs text-muted-foreground capitalize">{tech.category}</p>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-5 animate-fade-in">
            <div className="flex items-center gap-2 mb-2">
              <Code size={18} className="text-accent" />
              <h3 className="font-semibold">Review & Confirm</h3>
            </div>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-medium">Project Description</p>
                <p className="text-sm">{prompt}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">Tech Stack</p>
                <div className="flex flex-wrap gap-2">
                  {selectedTech.map(t => {
                    const tech = TECH_OPTIONS.find(o => o.id === t)
                    return (
                      <span key={t} className="px-3 py-1 rounded-lg text-xs font-medium bg-primary-500/10 text-primary-400 border border-primary-500/20">
                        {tech?.icon} {tech?.label}
                      </span>
                    )
                  })}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">Agents Involved</p>
                <div className="flex gap-3">
                  {['Architecture', 'Backend', 'Frontend', 'Review'].map(a => (
                    <div key={a} className="flex items-center gap-1 text-xs text-muted-foreground">
                      <div className="w-1.5 h-1.5 rounded-full bg-success" /> {a}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="flex flex-col items-center justify-center py-8 animate-fade-in text-center">
            {isSubmitting ? (
              <>
                <div className="w-16 h-16 rounded-full border-4 border-primary-500/20 border-t-primary-500 animate-spin mb-6" />
                <h3 className="text-xl font-bold mb-2">Forging Your Project</h3>
                <p className="text-muted-foreground text-sm max-w-sm">
                  Our AI agents are analyzing your requirements, designing the architecture, and generating code...
                </p>
              </>
            ) : (
              <>
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent/10 flex items-center justify-center mb-6">
                  <Sparkles size={28} className="text-accent" />
                </div>
                <h3 className="text-xl font-bold mb-2">Ready to Launch</h3>
                <p className="text-muted-foreground text-sm max-w-sm mb-6">
                  Click "Forge Project" to start the multi-agent pipeline. This typically takes 30-60 seconds.
                </p>
              </>
            )}
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep(s => Math.max(0, s - 1))}
          disabled={step === 0}
          className="btn-secondary disabled:opacity-30"
        >
          <ArrowLeft size={16} /> Back
        </button>
        <button
          onClick={nextStep}
          disabled={!canProceed() || isSubmitting}
          className="btn-primary"
        >
          {step === STEPS.length - 1 ? (
            isSubmitting ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Forging...</>
            ) : (
              <><Send size={16} /> Forge Project</>
            )
          ) : (
            <><span>Next</span> <ArrowRight size={16} /></>
          )}
        </button>
      </div>
    </div>
  )
}
