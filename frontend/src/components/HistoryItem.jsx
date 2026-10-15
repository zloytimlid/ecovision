import { Trash2 } from 'lucide-react'
import CategoryIcon from './CategoryIcon.jsx'
import { Link } from 'react-router-dom'

const STATUS_LABELS = {
  not_found: 'Не распознано',
  unmapped_class: 'Нет правил',
}

const dateFormat = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export default function HistoryItem({ item, onDelete, deleting }) {
  const title = item.category ? item.category.name : STATUS_LABELS[item.status] || item.top_class
  return (
    <li className="flex items-center gap-3 rounded-2xl border border-gray-200 p-2.5">
      <Link to={`/result/${item.id}`} className="flex min-w-0 flex-1 items-center gap-3">
        <img
          src={item.image_url}
          alt=""
          loading="lazy"
          className="h-16 w-16 shrink-0 rounded-xl bg-gray-100 object-cover"
        />
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 font-semibold">
            {item.category && (
              <CategoryIcon
                slug={item.category.slug}
                className="h-4 w-4 shrink-0"
                style={{ color: item.category.bin_color }}
              />
            )}
            <span className="truncate">{title}</span>
          </p>
          <p className="text-xs text-gray-500">
            {dateFormat.format(new Date(item.created_at))}
            {item.top_confidence != null && ` · ${Math.round(item.top_confidence * 100)}%`}
            {item.status === 'low_confidence' && ' · не уверены'}
          </p>
          {item.category && (
            <span
              className="mt-1 inline-block h-1.5 w-10 rounded-full"
              style={{ backgroundColor: item.category.bin_color }}
            />
          )}
        </div>
      </Link>
      <button
        type="button"
        onClick={() => onDelete(item)}
        disabled={deleting}
        aria-label="Удалить запись"
        className="rounded-lg p-2 text-gray-400 active:bg-red-50 active:text-red-600 disabled:opacity-40"
      >
        <Trash2 className="h-5 w-5" aria-hidden />
      </button>
    </li>
  )
}
