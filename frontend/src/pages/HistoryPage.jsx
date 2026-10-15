import { Camera, FolderOpen } from 'lucide-react'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { deleteRecognition, listRecognitions } from '../api/recognitions.js'
import ErrorMessage from '../components/ErrorMessage.jsx'
import HistoryItem from '../components/HistoryItem.jsx'
import Loader from '../components/Loader.jsx'
import useAuth from '../hooks/useAuth.jsx'

export default function HistoryPage() {
  const queryClient = useQueryClient()
  const { isLoggedIn } = useAuth()
  const query = useInfiniteQuery({
    queryKey: ['recognitions'],
    queryFn: ({ pageParam }) => listRecognitions(pageParam),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => (lastPage.next ? pages.length + 1 : undefined),
  })
  const removal = useMutation({
    mutationFn: (item) => deleteRecognition(item.id),
    onSuccess: (_, item) => {
      queryClient.removeQueries({ queryKey: ['recognition', item.id] })
      queryClient.invalidateQueries({ queryKey: ['recognitions'] })
    },
  })

  const handleDelete = (item) => {
    if (window.confirm('Удалить запись из истории?')) removal.mutate(item)
  }

  const items = query.data?.pages.flatMap((page) => page.results) ?? []

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">История</h1>
      {!isLoggedIn && (
        <p className="rounded-xl bg-gray-50 p-3 text-sm text-gray-600">
          История хранится на этом устройстве.{' '}
          <Link to="/login" className="font-medium text-emerald-700 underline">
            Войдите
          </Link>
          , чтобы она сохранялась в аккаунте.
        </p>
      )}
      {query.isPending && <Loader />}
      {query.isError && <ErrorMessage error={query.error} onRetry={() => query.refetch()} />}
      {removal.isError && <ErrorMessage error={removal.error} />}

      {query.isSuccess && items.length === 0 && (
        <div className="rounded-2xl border border-dashed border-gray-300 p-8 text-center">
          <FolderOpen className="mx-auto h-10 w-10 text-gray-400" aria-hidden />
          <p className="mt-2 font-semibold">Пока пусто</p>
          <p className="mt-1 text-sm text-gray-600">Здесь появятся ваши распознавания.</p>
          <Link to="/" className="mt-4 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 font-semibold text-white">
            <Camera className="h-5 w-5" aria-hidden /> Сфотографировать
          </Link>
        </div>
      )}

      <ul className="space-y-2">
        {items.map((item) => (
          <HistoryItem key={item.id} item={item} onDelete={handleDelete} deleting={removal.isPending} />
        ))}
      </ul>

      {query.hasNextPage && (
        <button
          type="button"
          onClick={() => query.fetchNextPage()}
          disabled={query.isFetchingNextPage}
          className="w-full rounded-xl border border-gray-300 py-2.5 font-medium text-gray-700 disabled:opacity-50"
        >
          {query.isFetchingNextPage ? 'Загрузка…' : 'Показать ещё'}
        </button>
      )}
    </div>
  )
}
