export default function TokenUsageBar({ current, max }: { current: number, max: number }) {
  const percentage = Math.min(100, Math.max(0, (current / max) * 100))
  const isWarning = percentage > 80
  const isDanger = percentage > 95

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted-foreground">Tokens Used</span>
        <span className="font-medium">{current.toLocaleString()} / {max.toLocaleString()}</span>
      </div>
      <div className="h-2 w-full bg-border rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ${isDanger ? 'bg-red-500' : isWarning ? 'bg-yellow-500' : 'bg-primary'}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
