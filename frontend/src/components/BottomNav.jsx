import { NavLink, useLocation } from 'react-router-dom'

const ITEMS = [
  { to: '/', icon: '📷', label: 'Сканер', match: (path) => path === '/' || path.startsWith('/result') },
  { to: '/history', icon: '🕘', label: 'История', match: (path) => path.startsWith('/history') },
  { to: '/catalog', icon: '📚', label: 'Справочник', match: (path) => path.startsWith('/catalog') },
  {
    to: '/profile',
    icon: '👤',
    label: 'Профиль',
    match: (path) => ['/profile', '/login', '/register'].includes(path),
  },
]

export default function BottomNav() {
  const { pathname } = useLocation()
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[480px] border-t border-gray-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      <ul className="grid grid-cols-4">
        {ITEMS.map((item) => {
          const active = item.match(pathname)
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-xs font-medium ${
                  active ? 'text-emerald-700' : 'text-gray-500'
                }`}
              >
                <span className="text-xl leading-none" aria-hidden>
                  {item.icon}
                </span>
                {item.label}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
