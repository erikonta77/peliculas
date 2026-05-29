import { useEffect, useState } from 'react'
import { Sparkles, ThumbsUp, ThumbsDown, Dices } from 'lucide-react'
import api from '../services/api'
import MovieCard from '../components/MovieCard'

interface Movie {
  id: string
  title: string
  poster_url?: string
  year?: number
  rating?: number
  genres: string[]
  reason?: string
  type?: string
}

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)
  const [rouletteMovie, setRouletteMovie] = useState<Movie | null>(null)

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const response = await api.get('/recommendations/personalized?count=12')
      const data = response.data
      setRecommendations(Array.isArray(data) ? data : data.recommendations || [])
    } catch (error) {
      console.error('Error fetching recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (movieId: string, accepted: boolean) => {
    try {
      await api.post('/recommendations/feedback', null, {
        params: { movie_id: movieId, accepted }
      })
      // Refresh recommendations
      fetchRecommendations()
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  const playRoulette = async () => {
    try {
      const response = await api.post('/recommendations/roulette')
      setRouletteMovie(response.data.roulette)
    } catch (error) {
      console.error('Error playing roulette:', error)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-primary-500" />
          Recomendaciones para Ti
        </h1>

        <button
          onClick={playRoulette}
          className="btn-secondary flex items-center gap-2"
        >
          <Dices className="w-5 h-5" />
          CineRoulette
        </button>
      </div>

      {/* Roulette Result */}
      {rouletteMovie && (
        <div className="card border-2 border-primary-500/50">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🎲</div>
            <div>
              <h3 className="text-lg font-semibold text-primary-400">
                ¡Sorpresa Cinematográfica!
              </h3>
              <p className="text-gray-400">
                Te recomendamos: {rouletteMovie.title} ({rouletteMovie.year})
              </p>
            </div>
            <button
              onClick={() => setRouletteMovie(null)}
              className="ml-auto btn-secondary"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

      {/* Recommendations Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <>
          {recommendations.length > 0 ? (
            <>
              <p className="text-gray-400">
                Basado en tus preferencias, estas películas podrían gustarte:
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {recommendations.map((movie) => (
                  <div key={movie.id} className="relative group">
                    <MovieCard movie={movie} />

                    {/* Feedback buttons */}
                    <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleFeedback(movie.id, true)}
                        className="p-2 bg-green-500 rounded-full hover:bg-green-600"
                      >
                        <ThumbsUp className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleFeedback(movie.id, false)}
                        className="p-2 bg-red-500 rounded-full hover:bg-red-600"
                      >
                        <ThumbsDown className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="card text-center py-12">
              <Sparkles className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                No hay recomendaciones aún
              </h3>
              <p className="text-gray-400">
                Configura tu perfil para recibir recomendaciones personalizadas.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
