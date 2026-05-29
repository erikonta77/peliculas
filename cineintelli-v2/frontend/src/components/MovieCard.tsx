import { Star } from 'lucide-react'

interface Movie {
  id: string
  title: string
  poster_url?: string
  year?: number
  rating?: number
  genres?: string[]
  reason?: string
  type?: string
}

interface MovieCardProps {
  movie: Movie
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

export default function MovieCard({ movie }: MovieCardProps) {
  return (
    <div className="card p-3 hover:scale-105 transition-transform cursor-pointer group flex flex-col h-full justify-between">
      <div>
        <div className="aspect-[2/3] rounded-lg overflow-hidden mb-3">
          {movie.poster_url ? (
            <img
              src={movie.poster_url}
              alt={movie.title}
              className="w-full h-full object-cover group-hover:opacity-90 transition-opacity"
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${getGradient(movie.title)} flex flex-col justify-between p-3 text-white shadow-inner relative`}>
              <div className="text-[10px] font-bold uppercase tracking-wider text-white/50">CineIntelli</div>
              <div className="text-sm font-extrabold leading-snug line-clamp-3 text-white drop-shadow-md">
                {movie.title}
              </div>
              <div className="text-[10px] font-medium text-white/70">
                {movie.year || 'N/A'}
              </div>
            </div>
          )}
        </div>
        <h3 className="font-medium text-sm line-clamp-2" title={movie.title}>
          {movie.title}
        </h3>
        <div className="flex items-center justify-between mt-2 text-sm text-gray-400">
          <span>{movie.year || 'N/A'}</span>
          {movie.rating && (
            <div className="flex items-center gap-1 text-yellow-500">
              <Star className="w-4 h-4 fill-current" />
              <span>{movie.rating.toFixed(1)}</span>
            </div>
          )}
        </div>
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {movie.genres.slice(0, 2).map((genre) => (
              <span
                key={genre}
                className="text-xs px-2 py-0.5 bg-dark-700 rounded-full text-gray-400"
              >
                {genre}
              </span>
            ))}
            {movie.type === 'exploration' && (
              <span className="text-[10px] px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded-full border border-purple-500/30 font-medium">
                Explorar 🎲
              </span>
            )}
          </div>
        )}
      </div>
      {movie.reason && (
        <div className="mt-3 text-xs text-primary-400 font-light border-t border-dark-600 pt-2 line-clamp-2" title={movie.reason}>
          💡 {movie.reason}
        </div>
      )}
    </div>
  )
}
