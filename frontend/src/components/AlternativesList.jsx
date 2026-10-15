import { Link } from 'react-router-dom'

export default function AlternativesList({ alternatives, onPick, selectedSlug, disabled }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
      {alternatives.length > 0 && (
        <>
          <p className="mb-2 text-sm font-semibold text-amber-900">Возможно, это:</p>
          <div className="flex flex-wrap gap-2">
            {alternatives.map((alt) => (
              <button
                key={alt.category_slug}
                type="button"
                disabled={disabled}
                onClick={() => onPick(alt.category_slug)}
                className={`rounded-full border px-3 py-1.5 text-sm font-medium transition disabled:opacity-60 ${
                  selectedSlug === alt.category_slug
                    ? 'border-emerald-600 bg-emerald-600 text-white'
                    : 'border-amber-300 bg-white text-amber-900 active:bg-amber-100'
                }`}
              >
                {alt.name} · {Math.round(alt.confidence * 100)}%
              </button>
            ))}
          </div>
        </>
      )}
      <Link to="/catalog" className="mt-2 inline-block text-sm font-medium text-emerald-700 underline">
        Найти в справочнике
      </Link>
    </div>
  )
}
