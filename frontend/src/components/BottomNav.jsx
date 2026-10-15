import { NavLink, useLocation } from 'react-router-dom'
import { NAV_ITEMS } from './navItems.js'

export default function BottomNav() {
  const { pathname } = useLocation()
  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[480px] border-t border-gray-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur">
      <ul className="grid grid-cols-4">
        {NAV_ITEMS.map((item) => {
          const active = item.match(pathname)
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={`flex flex-col items-center gap-0.5 py-2.5 text-xs font-medium ${
                  active ? 'text-emerald-700' : 'text-gray-500'
                }`}
              >
                <item.icon className="h-6 w-6" strokeWidth={active ? 2.25 : 1.75} aria-hidden />
                {item.label}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
