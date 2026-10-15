export default function ConfidenceBar({ value }) {
  const percent = Math.round((value || 0) * 100)
  const color = percent >= 60 ? 'bg-emerald-500' : percent >= 40 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-gray-600">
        <span>Уверенность модели</span>
        <span className="font-semibold">{percent}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}
