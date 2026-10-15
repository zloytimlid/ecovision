import { Check, ChevronLeft, ImageUp, KeyRound, Trash2, TriangleAlert, UserRound } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import Avatar from '../components/Avatar.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import Loader from '../components/Loader.jsx'
import useAuth from '../hooks/useAuth.jsx'
import { compressImage, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB } from '../utils/compressImage.js'

const inputClass =
  'mt-1 w-full rounded-xl border border-gray-300 px-4 py-2.5 font-normal outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200'
const primaryButton =
  'rounded-xl bg-emerald-600 px-5 py-2.5 font-semibold text-white active:bg-emerald-700 disabled:opacity-50 desktop:hover:bg-emerald-700'

/** Runs an async action and tracks its pending / error / success state. */
function useAction() {
  const [state, setState] = useState({ pending: false, error: null, done: false })
  const run = async (action) => {
    setState({ pending: true, error: null, done: false })
    try {
      await action()
      setState({ pending: false, error: null, done: true })
      return true
    } catch (error) {
      setState({ pending: false, error, done: false })
      return false
    }
  }
  return [state, run]
}

function Section({ icon: Icon, title, children, danger = false }) {
  return (
    <section className={`rounded-2xl border p-5 ${danger ? 'border-red-200' : 'border-gray-200'}`}>
      <h2 className={`mb-4 flex items-center gap-2 font-semibold ${danger ? 'text-red-700' : ''}`}>
        <Icon className="h-5 w-5" aria-hidden /> {title}
      </h2>
      {children}
    </section>
  )
}

function Saved({ text = 'Сохранено' }) {
  return (
    <p className="flex items-center gap-1.5 text-sm font-medium text-emerald-700" role="status">
      <Check className="h-4 w-4" aria-hidden /> {text}
    </p>
  )
}

function AvatarSection({ auth }) {
  const input = useRef(null)
  const [state, run] = useAction()
  const [localError, setLocalError] = useState(null)

  const onFile = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setLocalError('Выберите изображение в формате JPEG, PNG или WEBP.')
      return
    }
    setLocalError(null)
    await run(async () => {
      let blob
      try {
        blob = await compressImage(file, { maxSide: 512, quality: 0.9 })
      } catch {
        blob = file
      }
      if (blob.size > MAX_UPLOAD_BYTES) throw new Error(`Файл слишком большой — максимум ${MAX_UPLOAD_MB} МБ.`)
      await auth.uploadAvatar(blob)
    })
  }

  return (
    <Section icon={ImageUp} title="Аватар">
      <div className="flex items-center gap-4">
        <Avatar user={auth.user} size="h-20 w-20" textSize="text-3xl" />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={primaryButton}
            disabled={state.pending}
            onClick={() => input.current?.click()}
          >
            {state.pending ? 'Загружаем…' : auth.user.avatar_url ? 'Заменить' : 'Загрузить фото'}
          </button>
          {auth.user.avatar_url && (
            <button
              type="button"
              disabled={state.pending}
              onClick={() => run(() => auth.deleteAvatar())}
              className="rounded-xl border border-gray-300 px-4 py-2.5 font-medium text-gray-700 disabled:opacity-50 desktop:hover:bg-gray-50"
            >
              Удалить
            </button>
          )}
        </div>
      </div>
      <p className="mt-3 text-xs text-gray-500">Фото обрежется до квадрата. Геоданные и другие метаданные удаляются.</p>
      <input ref={input} type="file" accept="image/*" hidden onChange={onFile} />
      {(localError || state.error) && (
        <div className="mt-3">
          <ErrorMessage error={state.error} message={localError} />
        </div>
      )}
    </Section>
  )
}

function ProfileSection({ auth }) {
  const [username, setUsername] = useState(auth.user.username)
  const [email, setEmail] = useState(auth.user.email || '')
  const [state, run] = useAction()

  useEffect(() => {
    setUsername(auth.user.username)
    setEmail(auth.user.email || '')
  }, [auth.user.username, auth.user.email])

  const changed = username.trim() !== auth.user.username || email.trim() !== (auth.user.email || '')

  const submit = (event) => {
    event.preventDefault()
    run(() => auth.updateProfile({ username: username.trim(), email: email.trim() }))
  }

  return (
    <Section icon={UserRound} title="Профиль">
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
          <span className="mt-1 block text-xs font-normal text-gray-500">
            Буквы, цифры и символы @ . + - _. Используется для входа.
          </span>
        </label>
        <label className="block text-sm font-medium">
          E-mail <span className="font-normal text-gray-500">(необязательно)</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={inputClass}
          />
        </label>
        {state.error && <ErrorMessage error={state.error} />}
        <div className="flex items-center gap-4">
          <button type="submit" className={primaryButton} disabled={state.pending || !changed}>
            {state.pending ? 'Сохраняем…' : 'Сохранить'}
          </button>
          {state.done && !changed && <Saved />}
        </div>
      </form>
    </Section>
  )
}

function PasswordSection({ auth }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [repeat, setRepeat] = useState('')
  const [state, run] = useAction()
  const mismatch = repeat.length > 0 && next !== repeat

  const submit = async (event) => {
    event.preventDefault()
    if (mismatch) return
    if (await run(() => auth.changePassword(current, next))) {
      setCurrent('')
      setNext('')
      setRepeat('')
    }
  }

  return (
    <Section icon={KeyRound} title="Смена пароля">
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm font-medium">
          Текущий пароль
          <input
            required
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            className={inputClass}
          />
        </label>
        <label className="block text-sm font-medium">
          Новый пароль
          <input
            required
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            className={inputClass}
          />
          <span className="mt-1 block text-xs font-normal text-gray-500">
            Не короче 8 символов, не только цифры и не слишком простой.
          </span>
        </label>
        <label className="block text-sm font-medium">
          Повторите новый пароль
          <input
            required
            type="password"
            autoComplete="new-password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            className={inputClass}
          />
          {mismatch && <span className="mt-1 block text-xs font-normal text-red-600">Пароли не совпадают.</span>}
        </label>
        {state.error && <ErrorMessage error={state.error} />}
        <div className="flex flex-wrap items-center gap-4">
          <button type="submit" className={primaryButton} disabled={state.pending || mismatch}>
            {state.pending ? 'Меняем…' : 'Сменить пароль'}
          </button>
          {state.done && <Saved text="Пароль изменён. На других устройствах нужно войти заново." />}
        </div>
      </form>
    </Section>
  )
}

function DeleteSection({ auth }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState('')
  const [state, run] = useAction()

  const submit = async (event) => {
    event.preventDefault()
    if (await run(() => auth.deleteAccount(password))) navigate('/', { replace: true })
  }

  return (
    <Section icon={TriangleAlert} title="Удаление аккаунта" danger>
      <p className="text-sm text-gray-600">
        Аккаунт, история распознаваний и аватар будут удалены навсегда. Отменить это нельзя.
      </p>
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="mt-4 flex items-center gap-2 rounded-xl border border-red-300 px-4 py-2.5 font-medium text-red-700 active:bg-red-50 desktop:hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" aria-hidden /> Удалить аккаунт
        </button>
      ) : (
        <form onSubmit={submit} className="mt-4 space-y-3">
          <label className="block text-sm font-medium">
            Введите пароль для подтверждения
            <input
              required
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </label>
          {state.error && <ErrorMessage error={state.error} />}
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={state.pending}
              className="rounded-xl bg-red-600 px-5 py-2.5 font-semibold text-white active:bg-red-700 disabled:opacity-50 desktop:hover:bg-red-700"
            >
              {state.pending ? 'Удаляем…' : 'Удалить навсегда'}
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-xl border border-gray-300 px-4 py-2.5 font-medium text-gray-700 desktop:hover:bg-gray-50"
            >
              Отмена
            </button>
          </div>
        </form>
      )}
    </Section>
  )
}

export default function SettingsPage() {
  const auth = useAuth()

  if (!auth.isLoggedIn) return <Navigate to="/login" replace />
  if (auth.isLoading || !auth.user) return <Loader />

  return (
    <div className="space-y-4 desktop:mx-auto desktop:max-w-2xl">
      <Link to="/profile" className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700">
        <ChevronLeft className="h-4 w-4" aria-hidden /> Профиль
      </Link>
      <h1 className="text-xl font-bold desktop:text-2xl">Настройки</h1>
      <AvatarSection auth={auth} />
      <ProfileSection auth={auth} />
      <PasswordSection auth={auth} />
      <DeleteSection auth={auth} />
    </div>
  )
}
