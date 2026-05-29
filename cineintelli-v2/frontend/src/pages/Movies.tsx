import { useEffect, useState } from 'react'
import { Search, Filter } from 'lucide-react'
import api from '../services/api'
import MovieCard from '../components/MovieCard'

interface Movie {
  id: string
  title: string
  poster_url?: string
  year?: number
  rating?: number
  genres: string[]
}

export default function Movies() {
  const [movies, setMovies] = useState<Movie[]>([])
  const [genres, setGenres] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('')
  const [year, setYear] = useState('')
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const limit = 24

  useEffect(() => {
    fetchGenres()
    fetchMovies(0, true)
  }, [])

  const fetchGenres = async () => {
    try {
      const response = await api.get('/movies/genres')
      setGenres(response.data.genres)
    } catch (error) {
      console.error('Error fetching genres:', error)
    }
  }

  const fetchMovies = async (currentSkip = 0, reset = false) => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (selectedGenre) params.append('genre', selectedGenre)
      if (year) params.append('year', year)
      params.append('skip', currentSkip.toString())
      params.append('limit', limit.toString())

      const response = await api.get(`/movies/?${params}`)
      const newMovies = response.data.results || []
      
      if (reset) {
        setMovies(newMovies)
        setSkip(limit)
      } else {
        setMovies(prev => [...prev, ...newMovies])
        setSkip(currentSkip + limit)
      }
      setTotal(response.data.total || 0)
    } catch (error) {
      console.error('Error fetching movies:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchMovies(0, true)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Explorar Películas</h1>

      {/* Filters */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-5 h-5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar películas..."
                className="input pl-10"
              />
            </div>
          </div>

          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="input w-48"
          >
            <option value="">Todos los géneros</option>
            {genres.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>

          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            placeholder="Año"
            className="input w-32"
          />

          <button type="submit" className="btn-primary flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filtrar
          </button>
        </form>
      </div>

      {/* Results */}
      {loading && movies.length === 0 ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <>
          <p className="text-gray-400">
            Mostrando {movies.length} de {total} películas
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {movies.map((movie) => (
              <MovieCard key={movie.id} movie={movie} />
            ))}
          </div>

          {movies.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              No se encontraron películas con los filtros seleccionados.
            </div>
          )}

          {movies.length < total && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => fetchMovies(skip, false)}
                className="btn-secondary px-8 py-3 font-semibold hover:bg-dark-700 transition-colors flex items-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="animate-spin inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Cargando...
                  </>
                ) : (
                  'Cargar más películas'
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
