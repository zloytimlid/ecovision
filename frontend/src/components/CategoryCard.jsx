import { Link } from 'react-router-dom'

export default function CategoryCard({ category }) {
  return (
    <Link
      to={`/catalog/${category.slug}`}
      className="flex items-center gap-3 rounded-2xl border border-gray-200 p-3 active:bg-gray-50"
      style={{ borderLeft: `6px solid ${category.bin_color}` }}
    >
      <span className="text-3xl" aria-hidden>
        {category.icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold">
          {category.name}
          {category.is_hazardous && <span className="ml-1.5 text-xs font-bold text-red-600">⚠️ опасно</span>}
        </p>
        <p className="truncate text-sm text-gray-500">{category.bin_name}</p>
      </div>
      <span className="text-gray-400" aria-hidden>
        ›
      </span>
    </Link>
  )
}
