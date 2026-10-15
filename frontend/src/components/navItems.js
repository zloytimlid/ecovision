import { BookOpen, Camera, History, UserRound } from 'lucide-react'

export const NAV_ITEMS = [
  { to: '/', icon: Camera, label: 'Сканер', match: (path) => path === '/' || path.startsWith('/result') },
  { to: '/history', icon: History, label: 'История', match: (path) => path.startsWith('/history') },
  { to: '/catalog', icon: BookOpen, label: 'Справочник', match: (path) => path.startsWith('/catalog') },
  {
    to: '/profile',
    icon: UserRound,
    label: 'Профиль',
    match: (path) => ['/profile', '/settings', '/login', '/register'].includes(path),
  },
]
