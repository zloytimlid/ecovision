import { Recycle } from 'lucide-react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth.jsx'
import { NAV_ITEMS } from './navItems.js'

/** Header navigation for the desktop layout. */
export default function TopNav() {
  const { pathname } = useLocation()
  const { user } = useAuth()

  return (
    <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white">
            <Recycle className="h-5 w-5" aria-hidden />
          </span>
          <span className="text-lg font-bold text-emerald-800">EcoVision</span>
        </Link>
        <nav>
          <ul className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const active = item.match(pathname)
              const label = item.to === '/profile' && user ? user.username : item.label
              return (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition ${
                      active ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <item.icon className="h-4.5 w-4.5" aria-hidden />
                    {label}
                  </NavLink>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>
    </header>
  )
}
