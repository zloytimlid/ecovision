import { getErrorMessage } from '../utils/errors.js'

export default function ErrorMessage({ error, message, onRetry }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
      <p>{message || getErrorMessage(error)}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-lg bg-red-600 px-4 py-2 font-medium text-white active:bg-red-700"
        >
          Попробовать снова
        </button>
      )}
    </div>
  )
}
