import { Camera, Recycle, ScanSearch, Search, Trash2 } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { recognize } from '../api/recognitions.js'
import ErrorMessage from '../components/ErrorMessage.jsx'
import ImagePreview from '../components/ImagePreview.jsx'
import Loader from '../components/Loader.jsx'
import PhotoPicker from '../components/PhotoPicker.jsx'
import { compressImage, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB } from '../utils/compressImage.js'

async function prepareAndRecognize(file) {
  let blob
  try {
    blob = await compressImage(file)
  } catch {
    blob = file // e.g. a format the browser cannot decode; the server will validate it
  }
  if (blob.size > MAX_UPLOAD_BYTES) {
    throw new Error(`Фото слишком большое — максимум ${MAX_UPLOAD_MB} МБ.`)
  }
  return recognize(blob)
}

const STEPS = [
  { icon: Camera, text: 'Сфотографируйте предмет или загрузите фото' },
  { icon: ScanSearch, text: 'Нейросеть определит, что это за отход' },
  { icon: Trash2, text: 'Узнайте, в какой контейнер выбросить и как подготовить' },
]

export default function HomePage() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: prepareAndRecognize,
    onSuccess: (data) => {
      queryClient.setQueryData(['recognition', data.id], data)
      queryClient.invalidateQueries({ queryKey: ['recognitions'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      navigate(`/result/${data.id}`)
    },
  })

  useEffect(() => {
    if (!file) return undefined
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const selectFile = (selected) => {
    mutation.reset()
    setFile(selected)
  }

  return (
    <div className="space-y-5 desktop:grid desktop:grid-cols-[minmax(0,1fr)_minmax(0,460px)] desktop:items-center desktop:gap-14 desktop:space-y-0 desktop:py-4">
      <header className="pt-2 text-center desktop:pt-0 desktop:text-left">
        <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-sm desktop:mx-0 desktop:h-20 desktop:w-20">
          <Recycle className="h-9 w-9 desktop:h-11 desktop:w-11" aria-hidden />
        </span>
        <h1 className="mt-2 text-2xl font-bold text-emerald-800 desktop:mt-6 desktop:text-5xl">EcoVision</h1>
        <p className="mt-1 text-sm text-gray-600 desktop:mt-3 desktop:max-w-lg desktop:text-lg">
          Сфотографируйте предмет — подскажем, что это за отход и куда его выбросить.
        </p>
        <ol className="mt-8 hidden space-y-4 desktop:block">
          {STEPS.map(({ icon: Icon, text }, index) => (
            <li key={text} className="flex items-center gap-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                <Icon className="h-5 w-5" aria-hidden />
              </span>
              <span className="text-gray-700">
                <span className="font-semibold text-gray-900">{index + 1}.</span> {text}
              </span>
            </li>
          ))}
        </ol>
      </header>

      <div className="desktop:rounded-3xl desktop:border desktop:border-gray-200 desktop:bg-gray-50 desktop:p-6">
        {file && previewUrl ? (
          <div className="space-y-3">
            <ImagePreview src={previewUrl} />
            {mutation.isError && <ErrorMessage error={mutation.error} />}
            <button
              type="button"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate(file)}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-4 text-lg font-semibold text-white shadow-sm active:bg-emerald-700 disabled:opacity-50"
            >
              <Search className="h-5 w-5" aria-hidden />
              {mutation.isPending ? 'Анализируем…' : 'Определить'}
            </button>
            <button
              type="button"
              disabled={mutation.isPending}
              onClick={() => setFile(null)}
              className="w-full py-2 text-sm font-medium text-gray-600 disabled:opacity-50"
            >
              Выбрать другое фото
            </button>
          </div>
        ) : (
          <PhotoPicker onSelect={selectFile} />
        )}
      </div>

      {mutation.isPending && <Loader overlay text="Анализируем фото…" />}
    </div>
  )
}
