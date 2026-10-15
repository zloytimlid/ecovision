import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import ErrorMessage from '../components/ErrorMessage.jsx'
import useAuth from '../hooks/useAuth.jsx'

const TEXTS = {
  login: {
    title: 'Вход',
    submit: 'Войти',
    pending: 'Входим…',
    switchText: 'Нет аккаунта?',
    switchLink: 'Зарегистрироваться',
    switchTo: '/register',
  },
  register: {
    title: 'Регистрация',
    submit: 'Создать аккаунт',
    pending: 'Создаём…',
    switchText: 'Уже есть аккаунт?',
    switchLink: 'Войти',
    switchTo: '/login',
  },
}

export default function AuthPage({ mode }) {
  const auth = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [pending, setPending] = useState(false)
  const text = TEXTS[mode]

  if (auth.isLoggedIn) return <Navigate to="/profile" replace />

  const submit = async (event) => {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      await auth[mode](username, password)
      navigate('/profile', { replace: true })
    } catch (err) {
      setError(err)
      setPending(false)
    }
  }

  const inputClass =
    'mt-1 w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200'

  return (
    <div className="space-y-5 pt-4">
      <div className="text-center">
        <p className="text-4xl" aria-hidden>
          👤
        </p>
        <h1 className="mt-2 text-xl font-bold">{text.title}</h1>
        <p className="mt-1 text-sm text-gray-600">История распознаваний будет доступна на всех ваших устройствах.</p>
      </div>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm font-medium">
          Имя пользователя
          <input
            required
            autoComplete="username"
            autoCapitalize="none"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className={inputClass}
          />
        </label>
        <label className="block text-sm font-medium">
          Пароль
          <input
            required
            type="password"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
          {mode === 'register' && (
            <span className="mt-1 block text-xs font-normal text-gray-500">
              Не короче 8 символов, не только цифры и не слишком простой.
            </span>
          )}
        </label>
        {error && <ErrorMessage error={error} />}
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-2xl bg-emerald-600 py-3.5 text-lg font-semibold text-white active:bg-emerald-700 disabled:opacity-50"
        >
          {pending ? text.pending : text.submit}
        </button>
      </form>
      <p className="text-center text-sm text-gray-600">
        {text.switchText}{' '}
        <Link to={text.switchTo} replace className="font-medium text-emerald-700 underline">
          {text.switchLink}
        </Link>
      </p>
    </div>
  )
}
