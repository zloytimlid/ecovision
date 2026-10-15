import { TriangleAlert } from 'lucide-react'

export default function HazardBanner() {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-red-600 p-3 text-sm font-semibold text-white shadow" role="alert">
      <TriangleAlert className="h-5 w-5 shrink-0" aria-hidden />
      Опасный отход — не выбрасывайте в обычный контейнер
    </div>
  )
}
