import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, User } from 'lucide-react'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  
  // Mock authentication state for development
  const isAuthenticated = true
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  if (!isAuthenticated) return null

  return (
    <div className="relative">
      <div className="absolute top-4 right-4 flex items-center gap-4 z-50">
        <div className="flex items-center gap-2 bg-card border border-border px-3 py-1.5 rounded-full shadow-sm">
          <div className="w-6 h-6 bg-primary/20 text-primary rounded-full flex items-center justify-center">
            <User size={14} />
          </div>
          <span className="text-sm font-medium">Dev User</span>
          <button className="ml-2 text-muted-foreground hover:text-red-500 transition-colors">
            <LogOut size={16} />
          </button>
        </div>
      </div>
      {children}
    </div>
  )
}
