import { useState } from 'react'
import { Wrench, Loader2, CheckCircle, AlertTriangle, XCircle, MessageSquare, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react'
import axios from 'axios'
import type { FixResult } from '../types'

interface FixLoopPanelProps {
  projectId: string
  onOpenChat?: (context?: string) => void
  initialErrors?: string[]
}

export default function FixLoopPanel({ projectId, onOpenChat, initialErrors }: FixLoopPanelProps) {
  const [fixing, setFixing] = useState(false)
  const [result, setResult] = useState<FixResult | null>(null)
  const [currentStep, setCurrentStep] = useState('')
  const [iteration, setIteration] = useState(0)
  const [logsExpanded, setLogsExpanded] = useState(false)

  const handleStartFix = async () => {
    setFixing(true)
    setResult(null)
    setCurrentStep('Starting auto-fix...')
    setIteration(0)

    try {
      // Start fix loop
      const { data: startData } = await axios.post(`/api/projects/${projectId}/fix`)
      const fixId = startData.fix_id

      // Simulate step messages
      const steps = [
        'Analyzing errors...',
        'Debugger Agent fixing code...',
        'Review Agent checking fixes...',
        'Re-compiling project...',
      ]

      let stepIdx = 0
      const stepInterval = setInterval(() => {
        setCurrentStep(steps[stepIdx % steps.length])
        setIteration(prev => Math.min(prev + 1, 5))
        stepIdx++
      }, 3000)

      // Poll for result
      let pollCount = 0
      const maxPolls = 120

      const poll = async (): Promise<FixResult | null> => {
        if (pollCount >= maxPolls) return null
        pollCount++

        const { data } = await axios.get(`/api/projects/${projectId}/fix/${fixId}`)
        if (data.status === 'completed' && data.result) {
          return data.result as FixResult
        }

        await new Promise(r => setTimeout(r, 2000))
        return poll()
      }

      const fixResult = await poll()
      clearInterval(stepInterval)

      if (fixResult) {
        setResult(fixResult)
        setIteration(fixResult.iterations_used)
        setCurrentStep(fixResult.success ? 'All errors fixed!' : 'Fix loop completed')
      }
    } catch (e: any) {
      console.error(e)
      setCurrentStep('Fix loop failed')
    } finally {
      setFixing(false)
    }
  }

  const progressPercent = result
    ? result.success ? 100 : Math.round((result.errors_fixed.length / Math.max(result.errors_fixed.length + result.errors_remaining.length, 1)) * 100)
    : fixing ? Math.min(iteration * 20, 80) : 0

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Start Fix */}
      {!fixing && !result && (
        <div className="text-center py-10">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-white/[0.06] flex items-center justify-center mx-auto mb-4">
            <Wrench size={36} className="text-amber-400/60" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Auto-Fix Loop</h3>
          <p className="text-sm text-muted-foreground mb-2 max-w-md mx-auto">
            Automatically detect and fix compilation errors using AI agents. Up to 5 iterations.
          </p>
          {initialErrors && initialErrors.length > 0 && (
            <p className="text-xs text-amber-400 mb-4">
              {initialErrors.length} known error{initialErrors.length !== 1 ? 's' : ''} to fix
            </p>
          )}
          <button onClick={handleStartFix} className="btn-primary text-base px-8 py-3">
            <Wrench size={18} /> Start Auto-Fix
          </button>
        </div>
      )}

      {/* Progress */}
      {(fixing || result) && (
        <div className="glass-card-static p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold flex items-center gap-2">
              {result?.success ? (
                <><CheckCircle size={18} className="text-green-400" /> All Errors Fixed! ✅</>
              ) : result && result.errors_remaining.length > 0 ? (
                <><AlertTriangle size={18} className="text-amber-400" /> Partial Fix</>
              ) : result ? (
                <><XCircle size={18} className="text-red-400" /> Could Not Auto-Fix</>
              ) : (
                <><Loader2 size={18} className="text-indigo-400 animate-spin" /> Auto-Fix in Progress</>
              )}
            </h3>
            <span className="text-xs text-muted-foreground font-medium">
              Attempt {iteration || '...'} of 5
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2.5 bg-white/[0.04] rounded-full overflow-hidden mb-4">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                result?.success ? 'bg-gradient-to-r from-green-500 to-emerald-400' :
                result ? 'bg-gradient-to-r from-amber-500 to-orange-400' :
                'bg-gradient-to-r from-indigo-500 to-purple-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Current Step */}
          {fixing && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-500/5 border border-indigo-500/15 mb-4">
              <Loader2 size={14} className="text-indigo-400 animate-spin" />
              <span className="text-sm text-indigo-300">{currentStep}</span>
            </div>
          )}

          {/* Results Summary */}
          {result && (
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center px-3 py-3 rounded-xl bg-green-500/5 border border-green-500/10">
                <div className="text-lg font-bold text-green-400">{result.errors_fixed.length}</div>
                <div className="text-[10px] text-green-400/70 uppercase tracking-wider font-medium">Fixed</div>
              </div>
              <div className="text-center px-3 py-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
                <div className="text-lg font-bold text-amber-400">{result.errors_remaining.length}</div>
                <div className="text-[10px] text-amber-400/70 uppercase tracking-wider font-medium">Remaining</div>
              </div>
              <div className="text-center px-3 py-3 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
                <div className="text-lg font-bold text-indigo-400">{result.iterations_used}</div>
                <div className="text-[10px] text-indigo-400/70 uppercase tracking-wider font-medium">Iterations</div>
              </div>
            </div>
          )}

          {/* Fixed Errors */}
          {result && result.errors_fixed.length > 0 && (
            <div className="space-y-1.5 mb-4">
              <h4 className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <CheckCircle size={12} /> Errors Fixed
              </h4>
              {result.errors_fixed.slice(0, 5).map((err, i) => (
                <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-green-500/5 border border-green-500/10 text-xs">
                  <CheckCircle size={11} className="text-green-400 mt-0.5 shrink-0" />
                  <span className="text-green-300 font-mono break-words">{err}</span>
                </div>
              ))}
              {result.errors_fixed.length > 5 && (
                <p className="text-[10px] text-gray-500 px-3">...and {result.errors_fixed.length - 5} more</p>
              )}
            </div>
          )}

          {/* Remaining Errors */}
          {result && result.errors_remaining.length > 0 && (
            <div className="space-y-1.5 mb-4">
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <AlertTriangle size={12} /> Remaining Errors
              </h4>
              {result.errors_remaining.slice(0, 5).map((err, i) => (
                <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/10 text-xs">
                  <AlertTriangle size={11} className="text-amber-400 mt-0.5 shrink-0" />
                  <span className="text-amber-300 font-mono break-words">{err}</span>
                </div>
              ))}
            </div>
          )}

          {/* Logs */}
          {result?.logs && (
            <div>
              <button
                onClick={() => setLogsExpanded(!logsExpanded)}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-400 transition-colors"
              >
                {logsExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                View Logs
              </button>
              {logsExpanded && (
                <pre className="mt-2 p-3 rounded-lg bg-black/30 border border-white/[0.04] text-[10px] text-gray-500 font-mono overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {result.logs}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {result && (
        <div className="flex gap-3">
          <button onClick={handleStartFix} className="btn-secondary">
            <RotateCcw size={14} /> Re-run Fix Loop
          </button>
          {result.errors_remaining.length > 0 && onOpenChat && (
            <button
              onClick={() => onOpenChat(result.errors_remaining.join('\n'))}
              className="btn-primary"
            >
              <MessageSquare size={14} /> Chat to Fix
            </button>
          )}
        </div>
      )}
    </div>
  )
}
