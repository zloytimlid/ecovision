import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sendFeedback } from '../api/recognitions.js'

/** Sends feedback for a recognition and stores it in the cached result. */
export default function useFeedback(recognitionId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => sendFeedback(recognitionId, payload),
    onSuccess: (feedback) => {
      queryClient.setQueryData(['recognition', recognitionId], (old) => (old ? { ...old, feedback } : old))
      queryClient.invalidateQueries({ queryKey: ['recognitions'] })
    },
  })
}
