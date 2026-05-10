import { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Send, Trash2, ChevronDown, ChevronRight, Bot, User, Sparkles, Zap, Palette, Bug, RefreshCw } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import type { ChatMessage, FileChange } from '../types'

const SUGGESTION_CHIPS = [
  { label: 'Add authentication', icon: <Zap size={12} />, message: 'Add user authentication with JWT' },
  { label: 'Dark mode', icon: <Palette size={12} />, message: 'Add a dark mode toggle' },
  { label: 'Better UI', icon: <Sparkles size={12} />, message: 'Make the UI more modern with animations' },
  { label: 'Fix bugs', icon: <Bug size={12} />, message: 'Find and fix any bugs in the code' },
  { label: 'Add tests', icon: <RefreshCw size={12} />, message: 'Add unit tests for the main features' },
]

const AGENT_COLORS: Record<string, string> = {
  frontend: '#818cf8',
  backend: '#34d399',
  database: '#fbbf24',
  architecture: '#f472b6',
  debugger: '#ef4444',
  review: '#a78bfa',
}

/* ── File Changes Viewer ── */
function ChangesViewer({ changes }: { changes: FileChange[] }) {
  const [expanded, setExpanded] = useState(false)
  if (!changes || changes.length === 0) return null

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] font-medium text-primary-400 hover:text-primary-300 transition-colors"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        View Changes ({changes.length} file{changes.length !== 1 ? 's' : ''})
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5 animate-fade-in">
          {changes.map((change, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.05] text-[11px]"
            >
              <span className={`w-1.5 h-1.5 rounded-full ${
                change.action === 'created' ? 'bg-green-400' :
                change.action === 'deleted' ? 'bg-red-400' : 'bg-blue-400'
              }`} />
              <span className="text-gray-300 font-mono truncate flex-1">{change.file}</span>
              <span className={`text-[10px] font-medium uppercase tracking-wider ${
                change.action === 'created' ? 'text-green-400' :
                change.action === 'deleted' ? 'text-red-400' : 'text-blue-400'
              }`}>
                {change.action}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Agent Badges ── */
function AgentBadges({ agents }: { agents: string[] }) {
  if (!agents || agents.length === 0) return null
  return (
    <div className="flex gap-1 mt-2 flex-wrap">
      {agents.map(agent => (
        <span
          key={agent}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider"
          style={{
            backgroundColor: `${AGENT_COLORS[agent] || '#6366f1'}15`,
            color: AGENT_COLORS[agent] || '#6366f1',
            border: `1px solid ${AGENT_COLORS[agent] || '#6366f1'}30`,
          }}
        >
          <Bot size={9} />
          {agent}
        </span>
      ))}
    </div>
  )
}

/* ── Typing Indicator ── */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 py-3 px-4">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center shrink-0">
        <Bot size={13} className="text-indigo-400" />
      </div>
      <div className="flex gap-1 items-center">
        <div className="w-2 h-2 rounded-full bg-indigo-400/60 animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 rounded-full bg-indigo-400/60 animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 rounded-full bg-indigo-400/60 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-[11px] text-muted-foreground ml-1">NexusForge is thinking...</span>
    </div>
  )
}

/* ── Message Bubble ── */
function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-slide-up`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
        isUser
          ? 'bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/20'
          : 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20'
      }`}>
        {isUser ? <User size={13} className="text-blue-400" /> : <Bot size={13} className="text-indigo-400" />}
      </div>

      {/* Content */}
      <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-3.5 py-2.5 rounded-2xl text-[13px] leading-relaxed ${
          isUser
            ? 'bg-gradient-to-br from-blue-500/15 to-cyan-500/10 border border-blue-500/15 text-gray-200 rounded-br-md'
            : 'bg-white/[0.04] border border-white/[0.06] text-gray-300 rounded-bl-md'
        }`}>
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
        </div>

        {/* Changes viewer */}
        {message.changes && message.changes.length > 0 && (
          <ChangesViewer changes={message.changes} />
        )}

        {/* Agent badges */}
        {message.agents_involved && message.agents_involved.length > 0 && (
          <AgentBadges agents={message.agents_involved} />
        )}

        {/* Timestamp */}
        <div className={`text-[10px] text-muted-foreground mt-1 px-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

/* ── Main ChatPanel Component ── */
export default function ChatPanel({ projectId }: { projectId: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const { messages, sendMessage, isLoading, isStreaming, error, clearHistory } = useChat(projectId)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [hasUnread, setHasUnread] = useState(false)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Track unread messages when panel is closed
  useEffect(() => {
    if (!isOpen && messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      setHasUnread(true)
    }
  }, [messages, isOpen])

  // Clear unread when opening
  useEffect(() => {
    if (isOpen) setHasUnread(false)
  }, [isOpen])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    const msg = input.trim()
    setInput('')
    await sendMessage(msg)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChipClick = async (message: string) => {
    setInput('')
    await sendMessage(message)
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        id="chat-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 
          shadow-lg shadow-indigo-500/25 flex items-center justify-center transition-all duration-300 
          hover:shadow-xl hover:shadow-indigo-500/40 hover:scale-105 active:scale-95 group"
      >
        {isOpen ? (
          <X size={22} className="text-white" />
        ) : (
          <MessageSquare size={22} className="text-white group-hover:scale-110 transition-transform" />
        )}

        {/* Unread badge */}
        {hasUnread && !isOpen && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 border-2 border-[#050505] animate-pulse" />
        )}

        {/* Pulsing ring */}
        {hasUnread && !isOpen && (
          <span className="absolute inset-0 rounded-2xl border-2 border-indigo-400/50 animate-ping opacity-30" />
        )}
      </button>

      {/* Chat Panel */}
      <div
        className={`fixed top-0 right-0 z-40 h-full w-[400px] flex flex-col transition-transform duration-300 ease-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{
          background: 'rgba(10, 10, 15, 0.85)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles size={15} className="text-indigo-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">NexusForge Assistant</h3>
              <p className="text-[10px] text-muted-foreground">Modify your project with AI</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={clearHistory}
              className="p-2 rounded-lg text-muted-foreground hover:text-white hover:bg-white/[0.05] transition-colors"
              title="Clear history"
            >
              <Trash2 size={14} />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-lg text-muted-foreground hover:text-white hover:bg-white/[0.05] transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-6 gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-white/[0.06] flex items-center justify-center">
                <MessageSquare size={28} className="text-indigo-400/60" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-400 mb-1">Chat with NexusForge</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Ask me to add features, fix bugs, change the design, or modify your project in any way.
                </p>
              </div>

              {/* Suggestion chips */}
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {SUGGESTION_CHIPS.map((chip, i) => (
                  <button
                    key={i}
                    onClick={() => handleChipClick(chip.message)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium
                      bg-white/[0.04] border border-white/[0.08] text-gray-400
                      hover:bg-white/[0.08] hover:text-white hover:border-white/[0.15]
                      transition-all duration-200"
                  >
                    {chip.icon}
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} />
              ))}
              {(isLoading || isStreaming) && <TypingIndicator />}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mb-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {error}
          </div>
        )}

        {/* Input */}
        <div className="px-4 pb-4 pt-2 border-t border-white/[0.06]">
          {/* Suggestion chips (when messages exist) */}
          {messages.length > 0 && (
            <div className="flex gap-1.5 mb-2 overflow-x-auto pb-1 scrollbar-none">
              {SUGGESTION_CHIPS.slice(0, 3).map((chip, i) => (
                <button
                  key={i}
                  onClick={() => handleChipClick(chip.message)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-medium whitespace-nowrap
                    bg-white/[0.03] border border-white/[0.06] text-gray-500
                    hover:bg-white/[0.06] hover:text-gray-300 transition-all"
                >
                  {chip.icon}
                  {chip.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me to modify your project..."
              rows={1}
              className="flex-1 resize-none bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5
                text-[13px] text-gray-200 placeholder:text-gray-600 outline-none
                focus:border-indigo-500/40 focus:bg-white/[0.06] transition-all
                font-['Inter',sans-serif]"
              style={{ maxHeight: '120px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 
                flex items-center justify-center shrink-0 transition-all duration-200
                hover:shadow-lg hover:shadow-indigo-500/25 disabled:opacity-30 disabled:cursor-not-allowed
                disabled:hover:shadow-none active:scale-95"
            >
              <Send size={16} className="text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 backdrop-blur-[2px] transition-opacity duration-300"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
