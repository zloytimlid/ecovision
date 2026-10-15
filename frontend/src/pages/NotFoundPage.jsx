import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <p className="text-5xl" aria-hidden>
        🧭
      </p>
      <h1 className="mt-3 text-xl font-bold">Страница не найдена</h1>
      <Link to="/" className="mt-4 inline-block font-medium text-emerald-700 underline">
        На главную
      </Link>
    </div>
  )
}
