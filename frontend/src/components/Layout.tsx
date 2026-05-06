import { Outlet, Link } from 'react-router-dom'
import { LayoutDashboard, PlusCircle, Activity, Settings } from 'lucide-react'

export default function Layout() {
  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      <aside className="w-full md:w-64 bg-card border-r border-border p-4 flex flex-col gap-4">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center font-bold">N</div>
          <h1 className="text-xl font-bold tracking-tight">NexusForge</h1>
        </div>
        <nav className="flex flex-col gap-2 flex-grow">
          <Link to="/" className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition-colors">
            <LayoutDashboard size={18} /> Dashboard
          </Link>
          <Link to="/create" className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition-colors">
            <PlusCircle size={18} /> New Project
          </Link>
          <Link to="/agents" className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition-colors">
            <Activity size={18} /> Agents
          </Link>
        </nav>
        <div className="pt-4 border-t border-border mt-auto">
          <button className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition-colors w-full text-left text-muted-foreground">
            <Settings size={18} /> Settings
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
