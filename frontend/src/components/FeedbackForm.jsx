import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { useAllCategories } from '../api/categories.js'
import ErrorMessage from './ErrorMessage.jsx'

export default function FeedbackForm({ feedback, onSubmit, isPending, error }) {
  const { data: categories = [] } = useAllCategories()
  const [mode, setMode] = useState(null) // null | 'wrong'
  const [category, setCategory] = useState('')
  const [comment, setComment] = useState('')

  if (feedback && mode === null) {
    const picked = categories.find((c) => c.slug === feedback.correct_category)
    return (
      <div className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">
        <p className="font-semibold">Спасибо! Оценка сохранена.</p>
        <p className="mt-1">
          {feedback.is_correct
            ? 'Вы отметили результат как верный.'
            : `Правильная категория: ${picked?.name || feedback.correct_category}.`}
        </p>
        <button type="button" onClick={() => setMode('wrong')} className="mt-2 font-medium text-emerald-700 underline">
          Изменить оценку
        </button>
      </div>
    )
  }

  const submitWrong = (event) => {
    event.preventDefault()
    onSubmit({ is_correct: false, correct_category: category, comment }, () => setMode(null))
  }

  return (
    <div className="rounded-xl border border-gray-200 p-4">
      <p className="text-sm font-semibold">Результат верный?</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          type="button"
          disabled={isPending}
          onClick={() => onSubmit({ is_correct: true }, () => setMode(null))}
          className="flex items-center justify-center gap-2 rounded-xl border border-emerald-600 py-2.5 font-medium text-emerald-700 active:bg-emerald-50 disabled:opacity-50"
        >
          <ThumbsUp className="h-4 w-4" aria-hidden /> Да
        </button>
        <button
          type="button"
          disabled={isPending}
          onClick={() => setMode('wrong')}
          className={`flex items-center justify-center gap-2 rounded-xl border py-2.5 font-medium disabled:opacity-50 ${
            mode === 'wrong' ? 'border-red-600 bg-red-50 text-red-700' : 'border-gray-300 text-gray-700'
          }`}
        >
          <ThumbsDown className="h-4 w-4" aria-hidden /> Нет
        </button>
      </div>

      {mode === 'wrong' && (
        <form onSubmit={submitWrong} className="mt-4 space-y-3">
          <label className="block text-sm">
            <span className="font-medium">Правильная категория</span>
            <select
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 bg-white p-2.5"
            >
              <option value="">Выберите…</option>
              {categories.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium">Комментарий (необязательно)</span>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              placeholder="Например: это бумажный стаканчик"
              className="mt-1 w-full rounded-lg border border-gray-300 p-2.5"
            />
          </label>
          <button
            type="submit"
            disabled={isPending || !category}
            className="w-full rounded-xl bg-emerald-600 py-2.5 font-semibold text-white disabled:opacity-50"
          >
            {isPending ? 'Отправляем…' : 'Отправить'}
          </button>
        </form>
      )}
      {error && (
        <div className="mt-3">
          <ErrorMessage error={error} />
        </div>
      )}
    </div>
  )
}
