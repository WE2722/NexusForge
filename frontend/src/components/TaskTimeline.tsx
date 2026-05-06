import { Task } from '../types'
import { CheckCircle2, Circle, Clock, AlertCircle } from 'lucide-react'

export default function TaskTimeline({ tasks }: { tasks: Task[] }) {
  const getIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="text-green-500" size={20} />
      case 'in_progress': return <Clock className="text-primary animate-pulse" size={20} />
      case 'failed': return <AlertCircle className="text-red-500" size={20} />
      default: return <Circle className="text-muted-foreground" size={20} />
    }
  }

  return (
    <div className="space-y-4">
      {tasks.map((task, idx) => (
        <div key={task.id} className="flex gap-4 relative">
          {idx !== tasks.length - 1 && (
            <div className="absolute left-2.5 top-6 bottom-[-16px] w-[2px] bg-border z-0"></div>
          )}
          <div className="z-10 bg-card rounded-full mt-1">
            {getIcon(task.status)}
          </div>
          <div className="flex-1 pb-4">
            <h4 className="font-semibold text-sm">{task.title}</h4>
            <p className="text-xs text-muted-foreground mt-1 capitalize">{task.agent_type} Agent • Wave {task.wave}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
