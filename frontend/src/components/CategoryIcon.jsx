import {
  Apple,
  BatteryFull,
  Cylinder,
  Milk,
  Newspaper,
  Package,
  Recycle,
  Shirt,
  Smartphone,
  Trash2,
  Wine,
} from 'lucide-react'

// The backend also sends an emoji in category.icon; the UI uses these icons instead.
const ICONS = {
  plastic: Milk,
  paper: Newspaper,
  glass: Wine,
  metal: Cylinder,
  composite: Package,
  batteries: BatteryFull,
  electronics: Smartphone,
  organic: Apple,
  textile: Shirt,
  mixed: Trash2,
}

export default function CategoryIcon({ slug, className = 'h-6 w-6', ...props }) {
  const Icon = ICONS[slug] || Recycle
  return <Icon className={className} aria-hidden {...props} />
}
