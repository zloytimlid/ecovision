import { useState } from 'react'
import { Link } from 'react-router-dom'
import Loader from '../components/Loader.jsx'
import useAuth from '../hooks/useAuth.jsx'

const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

export default function ProfilePage() {
  const auth = useAuth()
  const [leaving, setLeaving] = useState(false)

  if (auth.isLoading) return <Loader />

  if (!auth.isLoggedIn) {
    return (
      <div className="space-y-4 pt-4 text-center">
        <p className="text-5xl" aria-hidden>
          👤
        </p>
        <h1 className="text-xl font-bold">Профиль</h1>
        <p className="text-sm text-gray-600">
          Сейчас история хранится только на этом устройстве. Войдите, чтобы она сохранялась в аккаунте и была доступна
          с любого телефона или компьютера.
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
    <div className="space-y-4 pt-4">
      <div className="rounded-2xl bg-emerald-50 p-5 text-center">
        <p className="text-5xl" aria-hidden>
          🌿
        </p>
        <h1 className="mt-2 text-xl font-bold">{auth.user?.username}</h1>
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
      <button
        type="button"
        onClick={logout}
        disabled={leaving}
        className="w-full rounded-2xl border border-gray-300 py-3 font-medium text-gray-700 disabled:opacity-50"
      >
        {leaving ? 'Выходим…' : 'Выйти'}
      </button>
    </div>
  )
}
