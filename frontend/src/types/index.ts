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

// ── Chat Types ──────────────────────────────────────────────────
export type ChatIntentType = 'add_feature' | 'fix_bug' | 'change_design' | 'refactor' | 'change_stack' | 'question'

export interface FileChange {
  file: string
  action: 'created' | 'modified' | 'deleted'
  diff: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  intent?: string
  changes?: FileChange[]
  agents_involved?: string[]
  status?: 'completed' | 'partial' | 'failed'
}

export interface ChatResponse {
  response: string
  intent: string
  changes: FileChange[]
  agents_involved: string[]
  status: 'completed' | 'partial' | 'failed'
  preview_url: string | null
}

// ── Compile / Fix / Delivery Types ──────────────────────────────
export interface CompileResult {
  id: string
  success: boolean
  backend_compiled: boolean
  frontend_compiled: boolean
  backend_errors: string[]
  frontend_errors: string[]
  backend_logs: string
  frontend_logs: string
  backend_url: string | null
  frontend_url: string | null
  temp_dir: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

export interface FixResult {
  id: string
  success: boolean
  iterations_used: number
  errors_fixed: string[]
  errors_remaining: string[]
  manual_fixes_needed: { file: string; error: string; suggestion: string }[]
  logs: string
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed'
}

export interface DeliveryResult {
  id: string
  download_url: string
  size_bytes: number
  zip_path: string
  readme_generated: boolean
  status: 'pending' | 'running' | 'completed' | 'failed'
}

export interface PreviewResult {
  id: string
  backend_url: string | null
  frontend_url: string | null
  expires_in: string
  status: 'running' | 'stopped' | 'failed'
}

