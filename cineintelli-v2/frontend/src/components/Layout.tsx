import { useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Film, Home, Sparkles, User, LogOut } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

export default function Layout() {
  const location = useLocation()
  const { user, setAuth, logout } = useAuthStore()

  useEffect(() => {
    if (!user) {
      setAuth('demo-token', {
        id: 'demo-user',
        email: 'demo@cineintelli.com',
        full_name: 'Usuario Demo'
      })
    }
  }, [user, setAuth])

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <Film className="w-8 h-8 text-primary-500" />
              <span className="text-xl font-bold">CineIntelli</span>
            </Link>

            <nav className="hidden md:flex items-center gap-6">
              <Link
                to="/"
                className={`flex items-center gap-2 transition-colors ${
                  isActive('/') ? 'text-primary-500' : 'text-gray-400 hover:text-white'
                }`}
              >
                <Home className="w-5 h-5" />
                Inicio
              </Link>
              <Link
                to="/movies"
                className={`flex items-center gap-2 transition-colors ${
                  isActive('/movies') ? 'text-primary-500' : 'text-gray-400 hover:text-white'
                }`}
              >
                <Film className="w-5 h-5" />
                Películas
              </Link>
              <Link
                to="/recommendations"
                className={`flex items-center gap-2 transition-colors ${
                  isActive('/recommendations') ? 'text-primary-500' : 'text-gray-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-5 h-5" />
                Recomendaciones
              </Link>
            </nav>

            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <Link to="/profile" className="flex items-center gap-2 text-gray-400 hover:text-white">
                    <User className="w-5 h-5" />
                    <span className="hidden sm:inline">{user.email}</span>
                  </Link>
                  <button onClick={logout} className="text-gray-400 hover:text-white">
                    <LogOut className="w-5 h-5" />
                  </button>
                </>
              ) : (
                <Link to="/login" className="btn-primary">
                  Iniciar Sesión
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
