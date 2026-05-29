import { useEffect, useState } from 'react'
import { Sparkles, Check, Film, Loader2 } from 'lucide-react'
import api from '../services/api'

interface Movie {
  id: string
  title: string
  display_title?: string
  poster_url?: string
  year?: number
  genres: string[]
}

interface OnboardingProps {
  onComplete: () => void
}

const getGradient = (str: string) => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    'from-rose-500 to-pink-600',
    'from-purple-600 to-indigo-600',
    'from-blue-500 to-cyan-500',
    'from-emerald-500 to-teal-500',
    'from-amber-500 to-orange-600',
    'from-violet-600 to-fuchsia-600',
    'from-sky-500 to-indigo-500',
    'from-red-500 to-rose-600',
  ]
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

export default function Onboarding({ onComplete }: OnboardingProps) {
  const [movies, setMovies] = useState<Movie[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchPopular()
  }, [])

  const fetchPopular = async () => {
    try {
      const response = await api.get('/movies/onboarding?limit=60')
      setMovies(response.data.results || [])
    } catch (error) {
      console.error('Error fetching onboarding movies:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    )
  }

  const handleFinish = async () => {
    if (selectedIds.length < 5) return
    setSaving(true)

    try {
      // 1. Enviar feedback positivo para cada película seleccionada
      for (const id of selectedIds) {
        await api.post(`/recommendations/feedback?movie_id=${id}&accepted=true`)
      }

      // 2. Inferir géneros favoritos a partir de las seleccionadas
      const selectedMovies = movies.filter(m => selectedIds.includes(m.id))
      const counts: Record<string, number> = {}
      selectedMovies.forEach(m => {
        if (m.genres) {
          m.genres.forEach(g => {
            counts[g] = (counts[g] || 0) + 1
          })
        }
      })
      const inferredGenres = Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(entry => entry[0])

      // 3. Actualizar perfil con géneros inferidos
      await api.put('/users/me/profile', {
        favorite_genres: inferredGenres,
        year_min: 1990,
        year_max: 2026,
        min_rating: 5.0
      })

      // 4. Marcar como completado y notificar
      localStorage.setItem('onboarding_completed', 'true')
      onComplete()
    } catch (error) {
      console.error('Error finishing onboarding:', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
        <p className="text-gray-400">Cargando catálogo para onboarding...</p>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-extrabold flex items-center justify-center gap-3 text-white">
          <Sparkles className="w-9 h-9 text-primary-500" />
          Personaliza tu CineIntelli
        </h1>
        <p className="text-lg text-gray-400 max-w-xl mx-auto">
          Selecciona al menos <strong className="text-primary-400">5 películas</strong> que te gusten para afinar al instante nuestro motor inteligente.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {movies.map(movie => {
          const isSelected = selectedIds.includes(movie.id)
          return (
            <div
              key={movie.id}
              onClick={() => toggleSelect(movie.id)}
              className={`card p-2 relative hover:scale-105 transition-transform cursor-pointer flex flex-col justify-between h-full border-2 ${
                isSelected ? 'border-primary-500 shadow-md ring-2 ring-primary-500/20' : 'border-transparent'
              }`}
            >
              <div>
                <div className="aspect-[2/3] rounded-lg overflow-hidden mb-2 relative">
                  {movie.poster_url ? (
                    <img
                      src={movie.poster_url}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className={`w-full h-full bg-gradient-to-br ${getGradient(movie.title)} flex flex-col justify-between p-2 text-white shadow-inner`}>
                      <div className="text-[8px] font-bold uppercase tracking-wider text-white/50">CineIntelli</div>
                      <div className="text-xs font-extrabold leading-snug line-clamp-3 text-white">
                        {movie.display_title || movie.title}
                      </div>
                      <div className="text-[8px] font-medium text-white/70">
                        {movie.year || 'N/A'}
                      </div>
                    </div>
                  )}
                  {isSelected && (
                    <div className="absolute inset-0 bg-primary-900/40 backdrop-blur-[1px] flex items-center justify-center">
                      <div className="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center shadow-lg">
                        <Check className="w-5 h-5 stroke-[3px]" />
                      </div>
                    </div>
                  )}
                </div>
                <h3 className="font-semibold text-xs text-white line-clamp-2" title={movie.display_title || movie.title}>
                  {movie.display_title || movie.title}
                </h3>
              </div>
            </div>
          )
        })}
      </div>

      <div className="sticky bottom-6 flex justify-center pt-6 bg-gradient-to-t from-dark-900 via-dark-900/90 to-transparent z-40">
        <button
          onClick={handleFinish}
          disabled={selectedIds.length < 5 || saving}
          className={`btn-primary px-8 py-4 text-base font-bold shadow-lg flex items-center gap-3 transition-all ${
            selectedIds.length >= 5 ? 'scale-105 hover:scale-110' : 'opacity-50 cursor-not-allowed'
          }`}
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Configurando tu motor...
            </>
          ) : (
            <>
              <Film className="w-5 h-5" />
              Comenzar mi Experiencia ({selectedIds.length}/5)
            </>
          )}
        </button>
      </div>
    </div>
  )
}
