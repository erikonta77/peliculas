import { Star } from 'lucide-react'

interface Movie {
  id: string
  title: string
  poster_url?: string
  year?: number
  rating?: number
  genres?: string[]
}

interface MovieCardProps {
  movie: Movie
}

export default function MovieCard({ movie }: MovieCardProps) {
  return (
    <div className="card p-3 hover:scale-105 transition-transform cursor-pointer group">
      <div className="aspect-[2/3] rounded-lg overflow-hidden bg-dark-700 mb-3">
        {movie.poster_url ? (
          <img
            src={movie.poster_url}
            alt={movie.title}
            className="w-full h-full object-cover group-hover:opacity-90 transition-opacity"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            Sin póster
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
        </div>
      )}
    </div>
  )
}
