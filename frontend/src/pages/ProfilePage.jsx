import { ChevronRight, LogOut, Settings, UserRound } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Avatar from '../components/Avatar.jsx'
import Loader from '../components/Loader.jsx'
import useAuth from '../hooks/useAuth.jsx'

const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

export default function ProfilePage() {
  const auth = useAuth()
  const [leaving, setLeaving] = useState(false)

  if (auth.isLoading) return <Loader />

  if (!auth.isLoggedIn) {
    return (
      <div className="space-y-4 pt-4 text-center desktop:mx-auto desktop:max-w-md desktop:py-6">
        <UserRound className="mx-auto h-12 w-12 text-emerald-600" aria-hidden />
        <h1 className="text-xl font-bold">Профиль</h1>
        <p className="text-sm text-gray-600">
          Сейчас история хранится только на этом устройстве. Войдите, чтобы она сохранялась в аккаунте и была доступна с
          любого телефона или компьютера.
        </p>
        <div className="grid gap-2">
          <Link to="/login" className="rounded-2xl bg-emerald-600 py-3.5 font-semibold text-white">
            Войти
          </Link>
          <Link to="/register" className="rounded-2xl border-2 border-emerald-600 py-3 font-semibold text-emerald-700">
            Зарегистрироваться
          </Link>
        </div>
      </div>
    )
  }

  const logout = async () => {
    setLeaving(true)
    await auth.logout()
    setLeaving(false)
  }

  return (
    <div className="space-y-4 pt-4 desktop:mx-auto desktop:max-w-md desktop:py-6">
      <div className="rounded-2xl bg-emerald-50 p-5 text-center">
        <div className="flex justify-center">
          <Avatar user={auth.user} size="h-20 w-20" textSize="text-3xl" />
        </div>
        <h1 className="mt-2 text-xl font-bold">{auth.user?.username}</h1>
        {auth.user?.email && <p className="text-sm text-gray-600">{auth.user.email}</p>}
        {auth.user && (
          <p className="mt-1 text-sm text-gray-600">С нами с {dateFormat.format(new Date(auth.user.date_joined))}</p>
        )}
      </div>
      {auth.user && (
        <Link to="/history" className="flex items-center justify-between rounded-2xl border border-gray-200 p-4">
          <span className="font-medium">Распознаваний в истории</span>
          <span className="text-xl font-bold text-emerald-700">{auth.user.recognitions_count}</span>
        </Link>
      )}
      <Link
        to="/settings"
        className="flex items-center justify-between rounded-2xl border border-gray-200 p-4 desktop:hover:bg-gray-50"
      >
        <span className="flex items-center gap-2 font-medium">
          <Settings className="h-5 w-5 text-gray-500" aria-hidden /> Настройки
        </span>
        <ChevronRight className="h-5 w-5 text-gray-400" aria-hidden />
      </Link>
      <button
        type="button"
        onClick={logout}
        disabled={leaving}
        className="flex w-full items-center justify-center gap-2 rounded-2xl border border-gray-300 py-3 font-medium text-gray-700 disabled:opacity-50"
      >
        <LogOut className="h-4 w-4" aria-hidden />
        {leaving ? 'Выходим…' : 'Выйти'}
      </button>
    </div>
  )
}
