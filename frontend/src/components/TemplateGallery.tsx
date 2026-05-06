import { Copy, Star } from 'lucide-react'

export default function TemplateGallery({ onSelect }: { onSelect: (template: any) => void }) {
  const templates = [
    { id: 1, name: 'SaaS Starter', desc: 'React, Node, Postgres, Stripe setup', tech: ['React', 'Postgres'] },
    { id: 2, name: 'E-Commerce', desc: 'Next.js storefront with inventory admin', tech: ['Next.js', 'Redis'] },
    { id: 3, name: 'AI Chatbot', desc: 'FastAPI + LangChain + React UI', tech: ['FastAPI', 'Python'] }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {templates.map(t => (
        <div key={t.id} className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors group cursor-pointer" onClick={() => onSelect(t)}>
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-semibold">{t.name}</h4>
            <Star size={14} className="text-yellow-500" />
          </div>
          <p className="text-xs text-muted-foreground mb-4 h-8">{t.desc}</p>
          <div className="flex justify-between items-center">
            <div className="flex gap-1">
              {t.tech.map(tech => <span key={tech} className="text-[10px] bg-muted px-1.5 py-0.5 rounded">{tech}</span>)}
            </div>
            <Copy size={14} className="text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        </div>
      ))}
    </div>
  )
}
