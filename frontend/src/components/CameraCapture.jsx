import { FolderOpen, SwitchCamera, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import useDevice from '../hooks/useDevice.jsx'

export function isCameraSupported() {
  // getUserMedia exists only in secure contexts (https or localhost).
  return Boolean(window.isSecureContext && navigator.mediaDevices?.getUserMedia)
}

function cameraErrorMessage(error) {
  switch (error?.name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'Нет доступа к камере. Разрешите доступ в настройках браузера или выберите файл.'
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'Камера не найдена. Выберите фото из файлов.'
    case 'NotReadableError':
      return 'Камера занята другим приложением. Закройте его и попробуйте снова.'
    default:
      return 'Не удалось включить камеру. Выберите фото из файлов.'
  }
}

/** Full-screen live camera preview; calls onCapture(File) with a JPEG snapshot. */
export default function CameraCapture({ onCapture, onClose, onPickFile }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const { isDesktop } = useDevice()
  // Computers usually have only a front-facing webcam.
  const [facingMode, setFacingMode] = useState(isDesktop ? 'user' : 'environment')
  const [canSwitch, setCanSwitch] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setReady(false)
    setError(null)

    navigator.mediaDevices
      .getUserMedia({
        video: { facingMode: { ideal: facingMode }, width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      })
      .then(async (stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop())
          return
        }
        streamRef.current = stream
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
        setReady(true)
        // Device labels and counts are available only after permission is granted.
        const devices = await navigator.mediaDevices.enumerateDevices()
        if (!cancelled) setCanSwitch(devices.filter((d) => d.kind === 'videoinput').length > 1)
      })
      .catch((err) => {
        if (!cancelled) setError(cameraErrorMessage(err))
      })

    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [facingMode])

  // Close on Escape (desktop).
  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const capture = () => {
    const video = videoRef.current
    if (!video?.videoWidth) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (!blob) return
        onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }))
      },
      'image/jpeg',
      0.92,
    )
  }

  const iconButton =
    'flex h-12 w-12 items-center justify-center rounded-full bg-white/15 text-white backdrop-blur active:bg-white/30'

  return (
    <div
      className="fixed inset-0 z-40 bg-black desktop:flex desktop:items-center desktop:justify-center desktop:bg-black/70 desktop:p-8 desktop:backdrop-blur-sm"
      role="dialog"
      aria-label="Камера"
      onClick={(event) => isDesktop && event.target === event.currentTarget && onClose()}
    >
      <div className="flex h-full w-full flex-col bg-black desktop:h-auto desktop:max-w-3xl desktop:overflow-hidden desktop:rounded-3xl desktop:shadow-2xl">
        <div className="relative flex-1 overflow-hidden desktop:aspect-video desktop:flex-none">
          <video
            ref={videoRef}
            playsInline
            muted
            className={`h-full w-full object-cover ${facingMode === 'user' ? '-scale-x-100' : ''}`}
          />
          {!ready && !error && (
            <p className="absolute inset-0 flex items-center justify-center text-sm text-white/80">Включаем камеру…</p>
          )}
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6 text-center text-white">
              <p>{error}</p>
              <button
                type="button"
                onClick={onPickFile}
                className="flex items-center gap-2 rounded-xl bg-white px-5 py-3 font-semibold text-gray-900"
              >
                <FolderOpen className="h-5 w-5" aria-hidden /> Выбрать файл
              </button>
            </div>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть камеру"
            className={`${iconButton} absolute top-4 right-4`}
          >
            <X className="h-6 w-6" aria-hidden />
          </button>
        </div>

        <div className="flex items-center justify-between px-8 pt-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]">
          <button type="button" onClick={onPickFile} aria-label="Выбрать файл" className={iconButton}>
            <FolderOpen className="h-6 w-6" aria-hidden />
          </button>
          <button
            type="button"
            onClick={capture}
            disabled={!ready}
            aria-label="Сделать снимок"
            className="h-18 w-18 rounded-full border-4 border-white bg-white/90 ring-4 ring-white/30 transition active:scale-95 disabled:opacity-40"
          />
          {canSwitch ? (
            <button
              type="button"
              onClick={() => setFacingMode((mode) => (mode === 'environment' ? 'user' : 'environment'))}
              aria-label="Переключить камеру"
              className={iconButton}
            >
              <SwitchCamera className="h-6 w-6" aria-hidden />
            </button>
          ) : (
            <span className="h-12 w-12" />
          )}
        </div>
      </div>
    </div>
  )
}
