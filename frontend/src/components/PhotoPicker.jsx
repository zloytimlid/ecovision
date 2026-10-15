import { Camera, FolderOpen, ImageUp } from 'lucide-react'
import { useRef, useState } from 'react'
import CameraCapture, { isCameraSupported } from './CameraCapture.jsx'

export default function PhotoPicker({ onSelect, disabled }) {
  const cameraInput = useRef(null)
  const fileInput = useRef(null)
  const [cameraOpen, setCameraOpen] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState(null)

  const select = (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError('Это не изображение. Выберите фото в формате JPEG, PNG или WEBP.')
      return
    }
    setError(null)
    setCameraOpen(false)
    onSelect(file)
  }

  const handleChange = (event) => {
    const file = event.target.files?.[0]
    event.target.value = '' // allow picking the same file again
    select(file)
  }

  const openCamera = () => {
    setError(null)
    // In-app camera needs https/localhost; otherwise use the phone's camera app.
    if (isCameraSupported()) setCameraOpen(true)
    else cameraInput.current?.click()
  }

  const openFiles = () => fileInput.current?.click()

  const dropProps = {
    onDragOver: (event) => {
      event.preventDefault()
      setDragging(true)
    },
    onDragLeave: (event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false)
    },
    onDrop: (event) => {
      event.preventDefault()
      setDragging(false)
      select(event.dataTransfer.files?.[0])
    },
  }

  const buttonClass =
    'flex w-full items-center justify-center gap-3 rounded-2xl px-5 py-5 text-lg font-semibold shadow-sm transition disabled:opacity-50'

  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        disabled={disabled}
        onClick={openCamera}
        className={`${buttonClass} bg-emerald-600 text-white active:bg-emerald-700`}
      >
        <Camera className="h-6 w-6" aria-hidden /> Сфотографировать
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={openFiles}
        className={`${buttonClass} border-2 border-emerald-600 bg-white text-emerald-700 active:bg-emerald-50`}
      >
        <FolderOpen className="h-6 w-6" aria-hidden /> Загрузить файл
      </button>

      {/* Drag & drop is only useful with a mouse, so the zone is hidden on touch screens. */}
      <div
        {...dropProps}
        onClick={openFiles}
        className={`hidden cursor-pointer flex-col items-center gap-1 rounded-2xl border-2 border-dashed p-5 text-center text-sm transition [@media(pointer:fine)]:flex ${
          dragging ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-300 text-gray-500'
        }`}
      >
        <ImageUp className="h-7 w-7" aria-hidden />
        Или перетащите фото сюда
      </div>

      {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden onChange={handleChange} />
      <input ref={fileInput} type="file" accept="image/*" hidden onChange={handleChange} />

      {cameraOpen && (
        <CameraCapture onCapture={select} onClose={() => setCameraOpen(false)} onPickFile={openFiles} />
      )}
    </div>
  )
}
