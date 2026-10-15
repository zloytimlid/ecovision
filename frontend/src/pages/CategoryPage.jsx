import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getCategory } from '../api/categories.js'
import ErrorMessage from '../components/ErrorMessage.jsx'
import HazardBanner from '../components/HazardBanner.jsx'
import Loader from '../components/Loader.jsx'
import { CategoryDetails } from '../components/ResultCard.jsx'
import { textColorOn } from '../utils/color.js'

function Chips({ title, items }) {
  if (!items?.length) return null
  return (
    <div>
      <h3 className="mb-1.5 text-sm font-semibold text-gray-800">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <span key={item} className="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700">
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function CategoryPage() {
  const { slug } = useParams()
  const query = useQuery({ queryKey: ['category', slug], queryFn: () => getCategory(slug) })

  return (
    <div className="space-y-4">
      <Link to="/catalog" className="text-sm font-medium text-emerald-700">
        ‹ Справочник
      </Link>
      {query.isPending && <Loader />}
      {query.isError && <ErrorMessage error={query.error} />}
      {query.isSuccess && (
        <>
          <div
            className="rounded-2xl p-5"
            style={{ backgroundColor: query.data.bin_color, color: textColorOn(query.data.bin_color) }}
          >
            <p className="text-4xl" aria-hidden>
              {query.data.icon}
            </p>
            <h1 className="mt-2 text-2xl font-bold">{query.data.name}</h1>
            {query.data.description && <p className="mt-1 text-sm opacity-90">{query.data.description}</p>}
          </div>
          {query.data.is_hazardous && <HazardBanner />}
          <CategoryDetails category={query.data} />
          <Chips title="Примеры предметов" items={query.data.examples} />
          <Chips title="Модель распознаёт" items={query.data.items} />
        </>
      )}
    </div>
  )
}
