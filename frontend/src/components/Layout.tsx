import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, PlusCircle, Activity, Settings, Zap, Key } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/create', icon: PlusCircle, label: 'New Project' },
  { to: '/agents', icon: Activity, label: 'Agent Network' },
  { to: '/keys', icon: Key, label: 'API Keys' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen mesh-bg flex">
      {/* Sidebar */}
      <aside className="w-64 min-h-screen glass-card-static border-r border-white/[0.06] p-5 flex flex-col fixed left-0 top-0 z-40">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10 px-1">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Zap size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">NexusForge</h1>
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-medium">AI Platform</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 flex-grow">
          {navItems.map(({ to, icon: Icon, label }) => {
            const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to))
            return (
              <Link
                key={to}
                to={to}
                className={`nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} />
                {label}
              </Link>
            )
          })}
        </nav>

        {/* Bottom status */}
        <div className="pt-4 mt-auto border-t border-white/[0.06]">
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs text-muted-foreground">System Online</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 ml-64 p-8 min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}
