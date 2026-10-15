export default function Loader({ text = 'Загрузка…', overlay = false }) {
  const content = (
    <div className="flex flex-col items-center gap-3 py-10 text-gray-600" role="status">
      <span className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
      <span className="text-sm font-medium">{text}</span>
    </div>
  )
  if (!overlay) return content
  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-white/80 backdrop-blur-sm">
      {content}
    </div>
  )
}
