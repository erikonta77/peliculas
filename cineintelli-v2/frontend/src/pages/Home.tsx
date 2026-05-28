import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, Film, TrendingUp } from 'lucide-react'
import api from '../services/api'
import MovieCard from '../components/MovieCard'

interface Movie {
  id: string
  title: string
  poster_url: string
  year: number
  rating: number
  genres: string[]
}

export default function Home() {
  const [popularMovies, setPopularMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPopular = async () => {
      try {
        const response = await api.get('/movies/popular?limit=6')
        setPopularMovies(response.data.results)
      } catch (error) {
        console.error('Error fetching popular movies:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPopular()
  }, [])

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-5xl font-bold mb-4">
          <span className="text-primary-500">Cine</span>Intelli
        </h1>
        <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          Descubre películas perfectas para ti usando inteligencia artificial.
          Nuestro sistema analiza tus preferencias y te recomienda lo mejor del cine.
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/recommendations" className="btn-primary flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Ver Recomendaciones
          </Link>
          <Link to="/movies" className="btn-secondary flex items-center gap-2">
            <Film className="w-5 h-5" />
            Explorar Catálogo
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-6">
        <div className="card text-center">
          <Sparkles className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">IA Avanzada</h3>
          <p className="text-gray-400">
            Nuestro autoencoder analiza patrones complejos para encontrar películas que te encantarán.
          </p>
        </div>
        <div className="card text-center">
          <TrendingUp className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Siempre Actualizado</h3>
          <p className="text-gray-400">
            Base de datos en constante crecimiento con las últimas películas y clásicos.
          </p>
        </div>
        <div className="card text-center">
          <Film className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">Catálogo Extenso</h3>
          <p className="text-gray-400">
            Miles de películas de todos los géneros, épocas y países disponibles.
          </p>
        </div>
      </section>

      {/* Popular Movies */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Películas Populares</h2>
          <Link to="/movies" className="text-primary-500 hover:text-primary-400">
            Ver todas →
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {popularMovies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
