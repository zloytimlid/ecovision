import { Camera } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRecognition } from '../api/recognitions.js'
import BoundingBoxOverlay from '../components/BoundingBoxOverlay.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import FeedbackForm from '../components/FeedbackForm.jsx'
import HazardBanner from '../components/HazardBanner.jsx'
import ImagePreview from '../components/ImagePreview.jsx'
import Loader from '../components/Loader.jsx'
import ResultCard from '../components/ResultCard.jsx'
import useFeedback from '../hooks/useFeedback.js'

export default function ResultPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const query = useQuery({ queryKey: ['recognition', id], queryFn: () => getRecognition(id) })
  const feedback = useFeedback(id)

  if (query.isPending) return <Loader />
  if (query.isError) {
    return (
      <div className="space-y-4">
        <ErrorMessage error={query.error} />
        <Link to="/" className="block text-center font-medium text-emerald-700 underline">
          На главную
        </Link>
      </div>
    )
  }

  const recognition = query.data
  const submitFeedback = (payload, onDone) => feedback.mutate(payload, { onSuccess: onDone })
  const pickAlternative = (slug) => submitFeedback({ is_correct: false, correct_category: slug })

  return (
    <div className="space-y-4 desktop:grid desktop:grid-cols-2 desktop:items-start desktop:gap-8 desktop:space-y-0">
      <div className="desktop:sticky desktop:top-24">
        <ImagePreview src={recognition.image_url}>
          <BoundingBoxOverlay objects={recognition.objects} imageSize={recognition.image_size} />
        </ImagePreview>
      </div>

      <div className="space-y-4">
        {recognition.has_hazardous && <HazardBanner />}

        <ResultCard
          recognition={recognition}
          onRetry={() => navigate('/')}
          onPickAlternative={pickAlternative}
          feedbackSlug={recognition.feedback?.correct_category}
          feedbackPending={feedback.isPending}
        />

        <FeedbackForm
          feedback={recognition.feedback}
          onSubmit={submitFeedback}
          isPending={feedback.isPending}
          error={feedback.error}
        />

        <button
          type="button"
          onClick={() => navigate('/')}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-4 text-lg font-semibold text-white shadow-sm active:bg-emerald-700 desktop:hover:bg-emerald-700"
        >
          <Camera className="h-5 w-5" aria-hidden /> Сфотографировать ещё
        </button>
      </div>
    </div>
  )
}
