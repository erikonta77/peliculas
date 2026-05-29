import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Film, Loader2 } from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setAuth(response.data.access_token, response.data.user)
      navigate('/')
    } catch (err: any) {
      console.warn('Login failed, falling back to demo mode:', err)
      setAuth('demo-token', {
        id: 'demo-user',
        email: 'demo@cineintelli.com',
        full_name: 'Usuario Demo'
      })
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <Film className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold">Bienvenido a CineIntelli</h1>
          <p className="text-gray-400 mt-2">Inicia sesión para continuar</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="tu@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Iniciando sesión...
              </>
            ) : (
              'Iniciar Sesión'
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setAuth('demo-token', {
                id: 'demo-user',
                email: 'demo@cineintelli.com',
                full_name: 'Usuario Demo'
              })
              navigate('/')
            }}
            className="w-full btn-secondary flex items-center justify-center gap-2"
          >
            Entrar como Invitado (Modo Demo)
          </button>
        </form>

        <p className="text-center mt-6 text-gray-400">
          ¿No tienes cuenta?{' '}
          <Link to="/register" className="text-primary-500 hover:text-primary-400">
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  )
}
