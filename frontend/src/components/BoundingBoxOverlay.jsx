import { useAllCategories } from '../api/categories.js'

const FALLBACK_COLOR = '#6b7280'

/**
 * Draws Roboflow boxes over the photo. Roboflow returns the box center (x, y)
 * and size in pixels of the processed image; they are converted to percentages
 * so the boxes scale with the displayed image.
 */
export default function BoundingBoxOverlay({ objects, imageSize }) {
  const { data: categories = [] } = useAllCategories()
  if (!objects?.length || !imageSize?.width || !imageSize?.height) return null

  const bySlug = Object.fromEntries(categories.map((c) => [c.slug, c]))
  const pct = (value, total) => `${(value / total) * 100}%`

  return (
    <div className="pointer-events-none absolute inset-0">
      {objects.map((obj, index) => {
        const { x, y, width, height } = obj.bbox
        const category = bySlug[obj.category_slug]
        const color = category?.bin_color || FALLBACK_COLOR
        return (
          <div
            key={index}
            className="absolute rounded-md border-[3px]"
            style={{
              left: pct(x - width / 2, imageSize.width),
              top: pct(y - height / 2, imageSize.height),
              width: pct(width, imageSize.width),
              height: pct(height, imageSize.height),
              borderColor: color,
            }}
          >
            <span
              className="absolute -top-0.5 left-0 -translate-y-full rounded px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap text-white"
              style={{ backgroundColor: color }}
            >
              {category?.icon} {category?.name || obj.model_class} · {Math.round(obj.confidence * 100)}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
