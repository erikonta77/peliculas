import { useEffect, useState } from 'react'
import { Save, User } from 'lucide-react'
import api from '../services/api'

interface ProfileData {
  favorite_genres: string[]
  year_min: number
  year_max: number
  min_rating: number
  preferred_language: string
  recommendations_count: number
}

export default function Profile() {
  const [genres, setGenres] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [profile, setProfile] = useState<ProfileData>({
    favorite_genres: [],
    year_min: 1900,
    year_max: 2024,
    min_rating: 0,
    preferred_language: 'any',
    recommendations_count: 10
  })

  useEffect(() => {
    fetchGenres()
    fetchProfile()
  }, [])

  const fetchGenres = async () => {
    try {
      const response = await api.get('/movies/genres')
      setGenres(response.data.genres)
    } catch (error) {
      console.error('Error fetching genres:', error)
    }
  }

  const fetchProfile = async () => {
    try {
      const response = await api.get('/users/me/profile')
      if (response.data) {
        setProfile(response.data)
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveProfile = async () => {
    setSaving(true)
    setMessage('')

    try {
      await api.put('/users/me/profile', profile)
      setMessage('Perfil guardado correctamente')
    } catch (error) {
      console.error('Error saving profile:', error)
      setMessage('Error al guardar el perfil')
    } finally {
      setSaving(false)
    }
  }

  const toggleGenre = (genre: string) => {
    setProfile(prev => ({
      ...prev,
      favorite_genres: prev.favorite_genres.includes(genre)
        ? prev.favorite_genres.filter(g => g !== genre)
        : [...prev.favorite_genres, genre]
    }))
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold flex items-center gap-3 mb-8">
        <User className="w-8 h-8 text-primary-500" />
        Tu Perfil
      </h1>

      {message && (
        <div className={`p-4 rounded-lg mb-6 ${
          message.includes('correctamente')
            ? 'bg-green-500/10 border border-green-500 text-green-500'
            : 'bg-red-500/10 border border-red-500 text-red-500'
        }`}>
          {message}
        </div>
      )}

      <div className="card space-y-6">
        {/* Genres */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Géneros Favoritos
          </label>
          <div className="flex flex-wrap gap-2">
            {genres.map((genre) => (
              <button
                key={genre}
                onClick={() => toggleGenre(genre)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  profile.favorite_genres.includes(genre)
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-gray-400 hover:bg-dark-600'
                }`}
              >
                {genre}
              </button>
            ))}
          </div>
        </div>

        {/* Year Range */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Rango de Años
          </label>
          <div className="flex items-center gap-4">
            <input
              type="number"
              value={profile.year_min}
              onChange={(e) => setProfile(prev => ({ ...prev, year_min: parseInt(e.target.value) }))}
              className="input w-32"
              min={1900}
              max={2024}
            />
            <span className="text-gray-400">hasta</span>
            <input
              type="number"
              value={profile.year_max}
              onChange={(e) => setProfile(prev => ({ ...prev, year_max: parseInt(e.target.value) }))}
              className="input w-32"
              min={1900}
              max={2024}
            />
          </div>
        </div>

        {/* Min Rating */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Puntuación Mínima: {profile.min_rating.toFixed(1)}
          </label>
          <input
            type="range"
            min={0}
            max={10}
            step={0.5}
            value={profile.min_rating}
            onChange={(e) => setProfile(prev => ({ ...prev, min_rating: parseFloat(e.target.value) }))}
            className="w-full"
          />
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Idioma Preferido
          </label>
          <select
            value={profile.preferred_language}
            onChange={(e) => setProfile(prev => ({ ...prev, preferred_language: e.target.value }))}
            className="input"
          >
            <option value="any">Cualquiera</option>
            <option value="es">Español</option>
            <option value="en">Inglés</option>
            <option value="fr">Francés</option>
            <option value="de">Alemán</option>
          </select>
        </div>

        {/* Recommendations Count */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Cantidad de Recomendaciones: {profile.recommendations_count}
          </label>
          <input
            type="range"
            min={5}
            max={50}
            step={5}
            value={profile.recommendations_count}
            onChange={(e) => setProfile(prev => ({ ...prev, recommendations_count: parseInt(e.target.value) }))}
            className="w-full"
          />
        </div>

        {/* Save Button */}
        <button
          onClick={saveProfile}
          disabled={saving}
          className="w-full btn-primary flex items-center justify-center gap-2"
        >
          <Save className="w-5 h-5" />
          {saving ? 'Guardando...' : 'Guardar Perfil'}
        </button>
      </div>
    </div>
  )
}
