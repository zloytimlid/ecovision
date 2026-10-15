import { ChevronRight, TriangleAlert } from 'lucide-react'
import CategoryIcon from './CategoryIcon.jsx'
import { Link } from 'react-router-dom'

export default function CategoryCard({ category }) {
  return (
    <Link
      to={`/catalog/${category.slug}`}
      className="flex items-center gap-3 rounded-2xl border border-gray-200 p-3 active:bg-gray-50"
      style={{ borderLeft: `6px solid ${category.bin_color}` }}
    >
      <span
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
        style={{ backgroundColor: `${category.bin_color}22`, color: category.bin_color }}
      >
        <CategoryIcon slug={category.slug} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-semibold">
          {category.name}
          {category.is_hazardous && (
            <span className="ml-1.5 inline-flex items-center gap-0.5 align-middle text-xs font-bold whitespace-nowrap text-red-600">
              <TriangleAlert className="h-3.5 w-3.5" aria-hidden /> опасно
            </span>
          )}
        </p>
        <p className="truncate text-sm text-gray-500">{category.bin_name}</p>
      </div>
      <ChevronRight className="h-5 w-5 shrink-0 text-gray-400" aria-hidden />
    </Link>
  )
}
