import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Layers, PlayCircle, PauseCircle } from 'lucide-react'
import { useProjects } from '../hooks/useProject'
import TaskTimeline from '../components/TaskTimeline'
import CodeViewer from '../components/CodeViewer'
import ProjectExport from '../components/ProjectExport'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { fetchProjectDetail, activeProject } = useProjects()
  const [activeTab, setActiveTab] = useState<'overview' | 'code'>('overview')

  useEffect(() => {
    if (id) {
      fetchProjectDetail(id)
      // Basic polling for updates (in real app, use SSE/WebSocket)
      const interval = setInterval(() => fetchProjectDetail(id), 3000)
      return () => clearInterval(interval)
    }
  }, [id])

  if (!activeProject) return <div className="p-8 text-center animate-pulse">Loading project details...</div>

  // Aggregate files from completed tasks
  const allFiles = activeProject.tasks.reduce((acc, task) => {
    if (task.result?.files_created && task.result?.code_blocks) {
      return { ...acc, ...task.result.code_blocks }
    }
    return acc
  }, {} as Record<string, string>)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">{activeProject.brief?.title || 'Project Setup'}</h2>
            <span className={`px-2 py-1 rounded text-xs font-medium uppercase tracking-wider ${activeProject.status === 'completed' ? 'bg-green-500/10 text-green-500' : activeProject.status === 'executing' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
              {activeProject.status}
            </span>
          </div>
          <p className="text-muted-foreground mt-2 max-w-2xl">{activeProject.brief?.description || activeProject.id}</p>
        </div>
        <div className="flex gap-2">
          {activeProject.status === 'executing' && (
             <button className="bg-muted hover:bg-muted/80 text-foreground px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm">
             <PauseCircle size={16} /> Pause
           </button>
          )}
          {activeProject.status === 'paused' && (
             <button className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md flex items-center gap-2 transition-colors text-sm">
             <PlayCircle size={16} /> Resume
           </button>
          )}
          {activeProject.status === 'completed' && (
             <ProjectExport project={activeProject} />
          )}
        </div>
      </div>

      <div className="flex border-b border-border">
        <button 
          onClick={() => setActiveTab('overview')} 
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${activeTab === 'overview' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
        >
          Overview & Timeline
        </button>
        <button 
          onClick={() => setActiveTab('code')} 
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${activeTab === 'code' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
        >
          Generated Code
        </button>
      </div>

      {activeTab === 'overview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><Layers size={18} /> Execution Plan</h3>
              <TaskTimeline tasks={activeProject.tasks} />
            </div>
          </div>
          <div className="space-y-6">
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Project Brief</h3>
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-muted-foreground block mb-1">Intent</span>
                  <p>{activeProject.brief?.intent}</p>
                </div>
                <div>
                  <span className="text-muted-foreground block mb-1">Tech Stack</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {activeProject.brief?.tech_stack.map(t => <span key={t} className="px-2 py-1 bg-muted rounded text-xs">{t}</span>)}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground block mb-1">Complexity</span>
                  <span className="capitalize">{activeProject.brief?.complexity}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg p-1">
           <CodeViewer files={allFiles} />
        </div>
      )}
    </div>
  )
}
