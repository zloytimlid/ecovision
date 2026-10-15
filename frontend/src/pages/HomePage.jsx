import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { recognize } from '../api/recognitions.js'
import ErrorMessage from '../components/ErrorMessage.jsx'
import ImagePreview from '../components/ImagePreview.jsx'
import Loader from '../components/Loader.jsx'
import PhotoPicker from '../components/PhotoPicker.jsx'
import { compressImage, MAX_UPLOAD_BYTES } from '../utils/compressImage.js'

async function prepareAndRecognize(file) {
  let blob
  try {
    blob = await compressImage(file)
  } catch {
    blob = file // e.g. a format the browser cannot decode; the server will validate it
  }
  if (blob.size > MAX_UPLOAD_BYTES) {
    throw new Error('Фото слишком большое — максимум 10 МБ.')
  }
  return recognize(blob)
}

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
    <div className="space-y-5">
      <header className="pt-2 text-center">
        <p className="text-5xl" aria-hidden>
          ♻️
        </p>
        <h1 className="mt-2 text-2xl font-bold text-emerald-800">EcoVision</h1>
        <p className="mt-1 text-sm text-gray-600">
          Сфотографируйте предмет — подскажем, что это за отход и куда его выбросить.
        </p>
      </header>

      {file && previewUrl ? (
        <div className="space-y-3">
          <ImagePreview src={previewUrl} />
          {mutation.isError && <ErrorMessage error={mutation.error} />}
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate(file)}
            className="w-full rounded-2xl bg-emerald-600 py-4 text-lg font-semibold text-white shadow-sm active:bg-emerald-700 disabled:opacity-50"
          >
            {mutation.isPending ? 'Анализируем…' : '🔍 Определить'}
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

      {mutation.isPending && <Loader overlay text="Анализируем фото…" />}
    </div>
  )
}
