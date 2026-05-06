export default function StatsCard({ title, value, icon, trend }: { title: string, value: string | number, icon: React.ReactNode, trend?: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-6 flex items-start gap-4 shadow-sm">
      <div className="p-3 bg-primary/10 text-primary rounded-lg">
        {icon}
      </div>
      <div>
        <p className="text-sm text-muted-foreground font-medium mb-1">{title}</p>
        <h3 className="text-2xl font-bold">{value}</h3>
        {trend && <p className="text-xs text-green-500 mt-1">{trend}</p>}
      </div>
    </div>
  )
}
