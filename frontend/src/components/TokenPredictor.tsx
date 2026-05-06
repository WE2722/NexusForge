import { Zap } from 'lucide-react'

export default function TokenPredictor({ estimatedTokens }: { estimatedTokens: number }) {
  const costPer1k = 0.0015 // average estimate
  const estimatedCost = ((estimatedTokens / 1000) * costPer1k).toFixed(4)
  
  return (
    <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <Zap size={16} className="text-primary" />
        <h4 className="font-medium text-sm text-primary">Token Prediction</h4>
      </div>
      <div className="flex justify-between items-end">
        <div>
          <p className="text-2xl font-bold">{estimatedTokens.toLocaleString()}</p>
          <p className="text-xs text-muted-foreground">Est. total tokens</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-green-500">${estimatedCost}</p>
          <p className="text-xs text-muted-foreground">Est. cost</p>
        </div>
      </div>
    </div>
  )
}
