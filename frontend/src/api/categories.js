import { useQuery } from '@tanstack/react-query'
import api from './client.js'

export async function listCategories(search = '') {
  const { data } = await api.get('/categories/', { params: search ? { search } : {} })
  return data
}

export async function getCategory(slug) {
  const { data } = await api.get(`/categories/${slug}/`)
  return data
}

/** Full category list, cached for the whole session (used for colors and pickers). */
export function useAllCategories() {
  return useQuery({
    queryKey: ['categories', ''],
    queryFn: () => listCategories(),
    staleTime: Infinity,
  })
}
