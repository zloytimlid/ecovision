import { useRef } from 'react'

export default function PhotoPicker({ onSelect, disabled }) {
  const cameraInput = useRef(null)
  const galleryInput = useRef(null)

  const handleChange = (event) => {
    const file = event.target.files?.[0]
    event.target.value = '' // allow picking the same file again
    if (file) onSelect(file)
  }

  const buttonClass =
    'flex w-full items-center justify-center gap-3 rounded-2xl px-5 py-5 text-lg font-semibold shadow-sm transition disabled:opacity-50'

  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        disabled={disabled}
        onClick={() => cameraInput.current?.click()}
        className={`${buttonClass} bg-emerald-600 text-white active:bg-emerald-700`}
      >
        <span className="text-2xl" aria-hidden>📷</span> Сфотографировать
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={() => galleryInput.current?.click()}
        className={`${buttonClass} border-2 border-emerald-600 bg-white text-emerald-700 active:bg-emerald-50`}
      >
        <span className="text-2xl" aria-hidden>🖼</span> Выбрать из галереи
      </button>
      <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden onChange={handleChange} />
      <input ref={galleryInput} type="file" accept="image/*" hidden onChange={handleChange} />
    </div>
  )
}
