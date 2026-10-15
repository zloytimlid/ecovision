import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { listCategories } from '../api/categories.js'
import CategoryCard from '../components/CategoryCard.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import Loader from '../components/Loader.jsx'

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function CatalogPage() {
  const [search, setSearch] = useState('')
  const query = useDebounced(search.trim())
  const categories = useQuery({
    queryKey: ['categories', query],
    queryFn: () => listCategories(query),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Справочник</h1>
      <input
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Поиск: бутылка, батарейка, газета…"
        className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
      />
      {categories.isPending && <Loader />}
      {categories.isError && <ErrorMessage error={categories.error} onRetry={() => categories.refetch()} />}
      {categories.isSuccess && categories.data.length === 0 && (
        <p className="py-8 text-center text-sm text-gray-500">Ничего не найдено. Попробуйте другое слово.</p>
      )}
      <div className="space-y-2">
        {categories.data?.map((category) => (
          <CategoryCard key={category.slug} category={category} />
        ))}
      </div>
    </div>
  )
}
