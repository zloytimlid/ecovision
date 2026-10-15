export default function BinBadge({ color, name }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-gray-50 p-3">
      <span
        className="h-9 w-9 shrink-0 rounded-lg border border-black/10 shadow-inner"
        style={{ backgroundColor: color }}
        aria-hidden
      />
      <p className="text-sm">
        <span className="font-semibold">Куда: </span>
        {name}
      </p>
    </div>
  )
}
