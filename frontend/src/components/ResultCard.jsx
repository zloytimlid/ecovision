import { Check, PackageX, ScanSearch, X } from 'lucide-react'
import CategoryIcon from './CategoryIcon.jsx'
import { Link } from 'react-router-dom'
import { textColorOn } from '../utils/color.js'
import AlternativesList from './AlternativesList.jsx'
import BinBadge from './BinBadge.jsx'
import ConfidenceBar from './ConfidenceBar.jsx'

function NotFound({ onRetry }) {
  return (
    <div className="rounded-2xl border border-gray-200 p-5">
      <ScanSearch className="h-9 w-9 text-gray-400" aria-hidden />
      <h2 className="mt-2 text-lg font-bold">Не удалось распознать предмет</h2>
      <p className="mt-2 text-sm text-gray-600">Попробуйте сфотографировать ещё раз:</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
        <li>снимите предмет крупнее;</li>
        <li>при хорошем освещении;</li>
        <li>один предмет на однотонном фоне.</li>
      </ul>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white active:bg-emerald-700"
      >
        Попробовать снова
      </button>
    </div>
  )
}

function Unmapped({ modelClass }) {
  return (
    <div className="rounded-2xl border border-gray-200 p-5">
      <PackageX className="h-9 w-9 text-gray-400" aria-hidden />
      <h2 className="mt-2 text-lg font-bold">Предмет распознан как «{modelClass}», но для него нет правил</h2>
      <p className="mt-2 text-sm text-gray-600">Найдите подходящую категорию вручную.</p>
      <Link to="/catalog" className="mt-3 inline-block font-medium text-emerald-700 underline">
        Открыть справочник
      </Link>
    </div>
  )
}

function ListBlock({ title, items, icon: Icon, iconClass }) {
  if (!items?.length) return null
  return (
    <div>
      <h3 className="mb-1.5 text-sm font-semibold text-gray-800">{title}</h3>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm text-gray-700">
            <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${iconClass}`} strokeWidth={2.5} aria-hidden />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CategoryDetails({ category }) {
  return (
    <>
      <BinBadge color={category.bin_color} name={category.bin_name} />
      <ListBlock title="Как подготовить" items={category.preparation_steps} icon={Check} iconClass="text-emerald-600" />
      <ListBlock title="Нельзя" items={category.do_not} icon={X} iconClass="text-red-600" />
    </>
  )
}

export default function ResultCard({ recognition, onRetry, onPickAlternative, feedbackSlug, feedbackPending }) {
  const { status, top, alternatives } = recognition

  if (status === 'not_found' || !top) return <NotFound onRetry={onRetry} />
  if (status === 'unmapped_class' || !top.category) return <Unmapped modelClass={top.model_class} />

  const { category } = top
  const isLow = status === 'low_confidence'
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-200 shadow-sm">
      <div className="p-4" style={{ backgroundColor: category.bin_color, color: textColorOn(category.bin_color) }}>
        <div className="flex items-center gap-3">
          <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white/25">
            <CategoryIcon slug={category.slug} className="h-8 w-8" />
          </span>
          <div>
            <p className="text-xs opacity-80">
              {top.display_name && top.display_name !== category.name ? `Похоже на: ${top.display_name}` : 'Тип отхода'}
            </p>
            <h2 className="text-xl leading-tight font-bold">{category.name}</h2>
          </div>
        </div>
        {isLow && (
          <span className="mt-3 inline-block rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-amber-800">
            Не уверены на 100%
          </span>
        )}
      </div>
      <div className="space-y-4 p-4">
        <ConfidenceBar value={top.confidence} />
        <CategoryDetails category={category} />
        {isLow && (
          <AlternativesList
            alternatives={alternatives}
            onPick={onPickAlternative}
            selectedSlug={feedbackSlug}
            disabled={feedbackPending}
          />
        )}
      </div>
    </div>
  )
}
