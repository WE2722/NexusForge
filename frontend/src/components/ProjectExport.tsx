import { useState } from 'react'
import { Download, Loader2, Play } from 'lucide-react'
import { Project } from '../types'

export default function ProjectExport({ project }: { project: Project }) {
  const [isExporting, setIsExporting] = useState(false)
  const [isLaunching, setIsLaunching] = useState(false)

  const handleExport = async () => {
    try {
      setIsExporting(true)
      const response = await fetch(`/api/projects/${project.id}/export`)
      
      if (!response.ok) {
        throw new Error('Export failed')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${project.brief?.title?.replace(/ /g, '_') || 'nexusforge_project'}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error exporting project:', error)
      alert('Failed to export project. Please ensure there are completed tasks with generated files.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleLaunch = async () => {
    try {
      setIsLaunching(true)
      const response = await fetch(`/api/projects/${project.id}/launch`, { method: 'POST' })
      
      if (!response.ok) {
        throw new Error('Launch failed')
      }
      
      alert('App successfully launched! Check the newly opened terminal windows on your desktop.')
    } catch (error) {
      console.error('Error launching project:', error)
      alert('Failed to launch project. Please ensure there are completed tasks with generated files.')
    } finally {
      setIsLaunching(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button 
        onClick={handleLaunch}
        disabled={isLaunching || isExporting}
        className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm font-medium disabled:opacity-50"
      >
        {isLaunching ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />} 
        {isLaunching ? 'Launching...' : 'Launch App'}
      </button>

      <button 
        onClick={handleExport}
        disabled={isExporting || isLaunching}
        className="bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm font-medium disabled:opacity-50"
      >
        {isExporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />} 
        {isExporting ? 'Exporting...' : 'Export ZIP'}
      </button>
    </div>
  )
}
