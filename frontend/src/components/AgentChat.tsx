import { Terminal, Bot } from 'lucide-react'

export default function AgentChat({ messages }: { messages: {agent: string, text: string}[] }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 h-64 flex flex-col">
      <div className="flex items-center gap-2 mb-4 border-b border-border pb-2">
        <Terminal size={16} className="text-primary" />
        <h3 className="font-semibold text-sm">Live Reasoning</h3>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">Waiting for agents to start...</p>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className="flex gap-2 text-sm">
              <Bot size={14} className="mt-1 flex-shrink-0 text-muted-foreground" />
              <div>
                <span className="font-medium capitalize text-xs text-primary">{msg.agent}: </span>
                <span className="text-muted-foreground">{msg.text}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
