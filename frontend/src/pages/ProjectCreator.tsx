import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Sparkles } from 'lucide-react'
import { useProjects } from '../hooks/useProject'

export default function ProjectCreator() {
  const [prompt, setPrompt] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { createProject } = useProjects()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    try {
      const project = await createProject(prompt)
      navigate(`/project/${project.id}`)
    } catch (err) {
      console.error(err)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create New Project</h2>
        <p className="text-muted-foreground mt-1">Describe what you want to build and NexusForge will handle the rest.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Build a real-time chat application with React, Tailwind, and FastAPI using WebSockets..."
            className="w-full h-64 p-4 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            required
            disabled={isSubmitting}
          />
          <div className="absolute bottom-4 right-4 text-muted-foreground flex items-center gap-2 text-sm">
            <Sparkles size={16} /> AI-Powered
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!prompt.trim() || isSubmitting}
            className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-3 rounded-md flex items-center gap-2 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin"></div>
                Initializing Agents...
              </>
            ) : (
              <>
                <Send size={18} /> Forge Project
              </>
            )}
          </button>
        </div>
      </form>
      
      <div className="bg-muted/30 p-4 rounded-lg border border-border">
        <h4 className="font-medium text-sm mb-2 flex items-center gap-2"><Sparkles size={16} className="text-primary"/> Pro Tips</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>Be specific about the technology stack (e.g., React, FastAPI, MongoDB)</li>
          <li>List the core features you need (e.g., Auth, Dashboard, Real-time updates)</li>
          <li>Mention any design preferences (e.g., Dark mode, Minimalist, Material Design)</li>
        </ul>
      </div>
    </div>
  )
}
