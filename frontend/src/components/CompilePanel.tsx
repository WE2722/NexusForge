import { useState } from 'react'
import { Package, Search, CheckCircle, Rocket, AlertTriangle, XCircle, Loader2, ChevronDown, ChevronRight, Wrench, MessageSquare } from 'lucide-react'
import axios from 'axios'
import type { CompileResult } from '../types'

interface CompileStep {
  id: string
  label: string
  icon: React.ReactNode
  status: 'pending' | 'running' | 'success' | 'error'
  detail?: string
}

interface CompilePanelProps {
  projectId: string
  onAutoFix?: () => void
  onChatFix?: (errorContext: string) => void
}

export default function CompilePanel({ projectId, onAutoFix, onChatFix }: CompilePanelProps) {
  const [compiling, setCompiling] = useState(false)
  const [result, setResult] = useState<CompileResult | null>(null)
  const [steps, setSteps] = useState<CompileStep[]>([
    { id: 'deps', label: 'Installing Dependencies', icon: <Package size={16} />, status: 'pending' },
    { id: 'types', label: 'Type Checking', icon: <Search size={16} />, status: 'pending' },
    { id: 'lint', label: 'Linting & Syntax', icon: <CheckCircle size={16} />, status: 'pending' },
    { id: 'servers', label: 'Starting Servers', icon: <Rocket size={16} />, status: 'pending' },
  ])
  const [errorsExpanded, setErrorsExpanded] = useState(false)

  const updateStep = (id: string, status: CompileStep['status'], detail?: string) => {
    setSteps(prev => prev.map(s => s.id === id ? { ...s, status, detail } : s))
  }

  const handleCompile = async () => {
    setCompiling(true)
    setResult(null)
    setSteps(prev => prev.map(s => ({ ...s, status: 'pending' as const, detail: undefined })))

    try {
      // Start compilation
      updateStep('deps', 'running')
      const { data: startData } = await axios.post(`/api/projects/${projectId}/compile`)
      const compileId = startData.compile_id

      // Simulate step progression while polling
      setTimeout(() => updateStep('deps', 'success'), 800)
      setTimeout(() => updateStep('types', 'running'), 1000)

      // Poll for result
      let pollCount = 0
      const maxPolls = 60 // 60 seconds max

      const poll = async (): Promise<CompileResult | null> => {
        if (pollCount >= maxPolls) return null
        pollCount++

        const { data } = await axios.get(`/api/projects/${projectId}/compile/${compileId}`)
        if (data.status === 'completed' && data.result) {
          return data.result as CompileResult
        }

        await new Promise(r => setTimeout(r, 1000))
        return poll()
      }

      const compileResult = await poll()

      if (compileResult) {
        setResult(compileResult)

        // Update steps based on result
        if (compileResult.backend_compiled) {
          updateStep('types', 'success')
          updateStep('lint', 'success')
        } else {
          updateStep('types', 'error', `${compileResult.backend_errors.length} error(s)`)
          updateStep('lint', 'error')
        }

        if (compileResult.frontend_compiled) {
          updateStep('servers', 'success')
        } else {
          updateStep('servers', 'error', `${compileResult.frontend_errors.length} error(s)`)
        }

        if (compileResult.success) {
          setSteps(prev => prev.map(s => ({ ...s, status: 'success' as const })))
        }
      } else {
        updateStep('types', 'error', 'Timeout')
        updateStep('lint', 'error')
        updateStep('servers', 'error')
      }
    } catch (e: any) {
      console.error(e)
      updateStep('deps', 'error', e.response?.data?.detail || 'Failed')
    } finally {
      setCompiling(false)
    }
  }

  const allErrors = result ? [...result.backend_errors, ...result.frontend_errors] : []

  const getStepIcon = (step: CompileStep) => {
    switch (step.status) {
      case 'running':
        return <Loader2 size={16} className="text-indigo-400 animate-spin" />
      case 'success':
        return <CheckCircle size={16} className="text-green-400" />
      case 'error':
        return <XCircle size={16} className="text-red-400" />
      default:
        return <span className="text-gray-600">{step.icon}</span>
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Compile Button */}
      {!compiling && !result && (
        <div className="text-center py-10">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-white/[0.06] flex items-center justify-center mx-auto mb-4">
            <Rocket size={36} className="text-indigo-400/60" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Compile Project</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
            Verify your generated code compiles correctly. We'll check syntax, types, imports, and try to start the servers.
          </p>
          <button onClick={handleCompile} className="btn-primary text-base px-8 py-3">
            <Rocket size={18} /> Start Compilation
          </button>
        </div>
      )}

      {/* Steps Progress */}
      {(compiling || result) && (
        <div className="glass-card-static p-6">
          <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
            {result?.success ? (
              <>
                <CheckCircle size={18} className="text-green-400" />
                Compilation Successful! 🎉
              </>
            ) : result ? (
              <>
                <AlertTriangle size={18} className="text-amber-400" />
                Compilation Found Issues
              </>
            ) : (
              <>
                <Loader2 size={18} className="text-indigo-400 animate-spin" />
                Compiling...
              </>
            )}
          </h3>

          <div className="space-y-3">
            {steps.map((step) => (
              <div
                key={step.id}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                  step.status === 'running' ? 'bg-indigo-500/5 border border-indigo-500/15' :
                  step.status === 'success' ? 'bg-green-500/5 border border-green-500/10' :
                  step.status === 'error' ? 'bg-red-500/5 border border-red-500/10' :
                  'bg-white/[0.02] border border-white/[0.04]'
                }`}
              >
                {getStepIcon(step)}
                <span className={`text-sm font-medium flex-1 ${
                  step.status === 'pending' ? 'text-gray-600' : 'text-gray-300'
                }`}>
                  {step.label}
                </span>
                {step.detail && (
                  <span className="text-xs text-muted-foreground">{step.detail}</span>
                )}
                {step.status === 'running' && (
                  <span className="text-[10px] text-indigo-400 font-medium animate-pulse">Running</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors Panel */}
      {allErrors.length > 0 && (
        <div className="glass-card-static p-5">
          <button
            onClick={() => setErrorsExpanded(!errorsExpanded)}
            className="flex items-center justify-between w-full text-left"
          >
            <div className="flex items-center gap-2">
              <XCircle size={16} className="text-red-400" />
              <span className="text-sm font-semibold text-red-400">
                {allErrors.length} Error{allErrors.length !== 1 ? 's' : ''} Found
              </span>
            </div>
            {errorsExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
          </button>

          {errorsExpanded && (
            <div className="mt-4 space-y-2 animate-fade-in">
              {allErrors.map((err, i) => (
                <div key={i} className="px-3 py-2.5 rounded-lg bg-red-500/5 border border-red-500/10 text-xs font-mono text-red-300 break-words">
                  {err}
                </div>
              ))}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={onAutoFix}
              className="btn-primary text-sm py-2"
            >
              <Wrench size={14} /> Auto-Fix
            </button>
            <button
              onClick={() => onChatFix?.(allErrors.join('\n'))}
              className="btn-secondary text-sm py-2"
            >
              <MessageSquare size={14} /> Fix Manually
            </button>
          </div>
        </div>
      )}

      {/* Success Actions */}
      {result?.success && (
        <div className="flex gap-3">
          <button onClick={handleCompile} className="btn-secondary">
            <Rocket size={14} /> Re-compile
          </button>
        </div>
      )}

      {/* Re-compile button after errors */}
      {result && !result.success && (
        <button onClick={handleCompile} className="btn-secondary w-full justify-center">
          <Rocket size={14} /> Re-compile
        </button>
      )}
    </div>
  )
}
