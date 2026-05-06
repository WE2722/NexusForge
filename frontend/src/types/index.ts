export type ProjectStatus = 'pending' | 'refining' | 'planning' | 'executing' | 'paused' | 'completed' | 'failed'
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'
export type AgentType = 'frontend' | 'backend' | 'database' | 'architecture' | 'debugger' | 'review'

export interface TokenUsage {
  provider: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface AgentResult {
  agent_type: AgentType
  task_id: string
  success: boolean
  output: string
  code_blocks: Record<string, string>
  files_created: string[]
  errors: string[]
  reasoning: string
}

export interface Task {
  id: string
  title: string
  description: string
  agent_type: AgentType
  status: TaskStatus
  result?: AgentResult
  wave: number
  completed_at?: string
}

export interface ProjectBrief {
  title: string
  description: string
  intent: string
  features: string[]
  tech_stack: string[]
  complexity: string
}

export interface Project {
  id: string
  status: ProjectStatus
  brief?: ProjectBrief
  tasks: Task[]
  created_at: string
}

export interface ProjectSummary {
  id: string
  title: string
  status: ProjectStatus
  task_count: number
  completed_tasks: number
  created_at: string
}

export interface AgentInfo {
  name: string
  agent_type: AgentType
  role: string
  expertise: string[]
  preferred_providers: string[]
}
