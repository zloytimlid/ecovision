import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <Compass className="mx-auto h-12 w-12 text-gray-400" aria-hidden />
      <h1 className="mt-3 text-xl font-bold">Страница не найдена</h1>
      <Link to="/" className="mt-4 inline-block font-medium text-emerald-700 underline">
        На главную
      </Link>
    </div>
  )
}
