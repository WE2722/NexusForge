import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Layers, PlayCircle, PauseCircle, Download, Rocket, Check, Clock, AlertCircle, Loader2, Code, FileText } from 'lucide-react'
import { useProjects } from '../hooks/useProject'
import axios from 'axios'

/* ── Timeline Component ── */
function TaskTimeline({ tasks }: { tasks: any[] }) {
  const grouped: Record<number, any[]> = {}
  tasks.forEach(t => { grouped[t.wave] = [...(grouped[t.wave] || []), t] })

  const getIcon = (status: string) => {
    switch (status) {
      case 'completed': return <Check size={14} className="text-success" />
      case 'in_progress': return <Loader2 size={14} className="text-primary-400 animate-spin" />
      case 'failed': return <AlertCircle size={14} className="text-danger" />
      default: return <Clock size={14} className="text-muted-foreground" />
    }
  }

  return (
    <div className="space-y-4">
      {Object.entries(grouped).sort(([a], [b]) => +a - +b).map(([wave, waveTasks]) => (
        <div key={wave} className="relative">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground bg-white/[0.04] px-2.5 py-1 rounded-md">
              Wave {wave}
            </span>
          </div>
          <div className="space-y-1 ml-1 border-l border-white/[0.06] pl-4">
            {waveTasks.map(task => (
              <div key={task.id} className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.02] transition-colors">
                {getIcon(task.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{task.title}</p>
                  <p className="text-xs text-muted-foreground capitalize">{task.agent_type} agent</p>
                </div>
                <span className={`status-badge text-[10px] ${
                  task.status === 'completed' ? 'status-completed' :
                  task.status === 'in_progress' ? 'status-executing' :
                  task.status === 'failed' ? 'status-failed' : 'status-pending'
                }`}>
                  {task.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/* ── Code Viewer ── */
function CodeViewer({ files }: { files: Record<string, string> }) {
  const fileNames = Object.keys(files)
  const [activeFile, setActiveFile] = useState(fileNames[0] || '')

  if (fileNames.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Code size={32} className="mx-auto mb-3 opacity-50" />
        <p>No code generated yet.</p>
      </div>
    )
  }

  return (
    <div className="flex h-[500px] rounded-xl overflow-hidden border border-white/[0.06]">
      {/* File sidebar */}
      <div className="w-52 bg-black/30 border-r border-white/[0.06] overflow-y-auto shrink-0">
        <div className="p-2 text-[10px] text-muted-foreground uppercase tracking-wider font-bold px-3 py-2">
          Files ({fileNames.length})
        </div>
        {fileNames.map(name => (
          <button
            key={name}
            onClick={() => setActiveFile(name)}
            className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 transition-colors ${
              activeFile === name ? 'bg-primary-500/10 text-primary-400' : 'text-muted-foreground hover:text-white hover:bg-white/[0.03]'
            }`}
          >
            <FileText size={12} />
            <span className="truncate">{name}</span>
          </button>
        ))}
      </div>
      {/* Code area */}
      <div className="flex-1 overflow-auto bg-black/20">
        <div className="px-3 py-2 text-xs text-muted-foreground border-b border-white/[0.06] bg-black/20 sticky top-0">
          {activeFile}
        </div>
        <pre className="p-4 text-xs font-mono leading-relaxed whitespace-pre-wrap break-words text-gray-300">
          {files[activeFile] || ''}
        </pre>
      </div>
    </div>
  )
}

/* ── Main Component ── */
export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { fetchProjectDetail, activeProject } = useProjects()
  const [activeTab, setActiveTab] = useState<'overview' | 'code'>('overview')
  const [launching, setLaunching] = useState(false)

  useEffect(() => {
    if (id) {
      fetchProjectDetail(id)
      const interval = setInterval(() => fetchProjectDetail(id), 3000)
      return () => clearInterval(interval)
    }
  }, [id])

  const handleLaunch = async () => {
    if (!id) return
    setLaunching(true)
    try {
      await axios.post(`/api/projects/${id}/launch`)
    } catch (e) {
      console.error(e)
    } finally {
      setLaunching(false)
    }
  }

  const handleExport = async () => {
    if (!id) return
    try {
      const resp = await axios.get(`/api/projects/${id}/export`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `${activeProject?.brief?.title?.replace(/\s/g, '_') || 'project'}.zip`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error(e)
    }
  }

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-primary-500/20 border-t-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading project details...</p>
        </div>
      </div>
    )
  }

  const allFiles = activeProject.tasks.reduce((acc, task) => {
    if (task.result?.code_blocks) {
      return { ...acc, ...task.result.code_blocks }
    }
    return acc
  }, {} as Record<string, string>)

  const completedTasks = activeProject.tasks.filter(t => t.status === 'completed').length
  const progress = activeProject.tasks.length > 0 ? (completedTasks / activeProject.tasks.length) * 100 : 0

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-3xl font-bold tracking-tight">{activeProject.brief?.title || 'Project'}</h2>
            <span className={`status-badge ${
              activeProject.status === 'completed' ? 'status-completed' :
              activeProject.status === 'executing' ? 'status-executing' :
              activeProject.status === 'failed' ? 'status-failed' : 'status-pending'
            }`}>
              {activeProject.status}
            </span>
          </div>
          <p className="text-muted-foreground max-w-2xl text-sm">{activeProject.brief?.description}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          {activeProject.status === 'completed' && (
            <>
              <button onClick={handleExport} className="btn-secondary">
                <Download size={16} /> Export ZIP
              </button>
              <button onClick={handleLaunch} disabled={launching} className="btn-primary">
                {launching ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
                {launching ? 'Launching...' : 'Launch App'}
              </button>
            </>
          )}
          {activeProject.status === 'executing' && (
            <button className="btn-secondary">
              <PauseCircle size={16} /> Pause
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {activeProject.status === 'executing' && (
        <div className="glass-card-static p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-medium">Progress</span>
            <span className="text-xs font-bold text-primary-400">{Math.round(progress)}%</span>
          </div>
          <div className="w-full h-2 bg-white/[0.04] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-accent rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-white/[0.02] rounded-xl w-fit">
        {(['overview', 'code'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all capitalize ${
              activeTab === tab
                ? 'bg-white/[0.06] text-white'
                : 'text-muted-foreground hover:text-white'
            }`}
          >
            {tab === 'overview' ? 'Overview & Timeline' : 'Generated Code'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-card-static p-6">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <Layers size={16} className="text-accent" /> Execution Plan
            </h3>
            <TaskTimeline tasks={activeProject.tasks} />
          </div>
          <div className="space-y-5">
            <div className="glass-card-static p-6">
              <h3 className="text-base font-semibold mb-4">Project Brief</h3>
              <div className="space-y-4 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium block mb-1">Intent</span>
                  <p className="text-gray-300">{activeProject.brief?.intent}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium block mb-2">Tech Stack</span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeProject.brief?.tech_stack.map(t => (
                      <span key={t} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-white/[0.04] border border-white/[0.06] text-gray-300">{t}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium block mb-1">Complexity</span>
                  <span className="capitalize text-gray-300">{activeProject.brief?.complexity}</span>
                </div>
              </div>
            </div>
            <div className="glass-card-static p-6">
              <h3 className="text-base font-semibold mb-3">Stats</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Tasks</span>
                  <span className="font-medium">{activeProject.tasks.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Completed</span>
                  <span className="font-medium text-success">{completedTasks}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Files Generated</span>
                  <span className="font-medium">{Object.keys(allFiles).length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <CodeViewer files={allFiles} />
      )}
    </div>
  )
}
