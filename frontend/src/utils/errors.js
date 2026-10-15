const MESSAGES = {
  invalid_image: 'Файл не похож на фото. Выберите изображение в формате JPEG, PNG или WEBP.',
  missing_client_id: 'Не удалось определить устройство. Обновите страницу.',
  file_too_large: 'Фото слишком большое — максимум 10 МБ.',
  throttled: 'Слишком много запросов. Подождите минуту и попробуйте снова.',
  model_unavailable: 'Сервис распознавания временно недоступен. Попробуйте позже.',
  model_timeout: 'Распознавание заняло слишком много времени. Попробуйте ещё раз.',
  not_found: 'Запись не найдена — возможно, она была удалена.',
  not_authenticated: 'Войдите в аккаунт.',
  authentication_failed: 'Сессия истекла — войдите снова.',
}

/** Human-readable Russian message for an API / network / local error. */
export function getErrorMessage(error) {
  const apiError = error?.response?.data?.error
  if (apiError) {
    if (apiError.code === 'validation_error') return apiError.message
    return MESSAGES[apiError.code] || apiError.message || 'Что-то пошло не так.'
  }
  if (error?.code === 'ECONNABORTED') return 'Сервер не ответил вовремя. Попробуйте ещё раз.'
  if (error?.response) return `Ошибка сервера (${error.response.status}). Попробуйте позже.`
  if (error?.request) return 'Нет связи с сервером. Проверьте интернет и попробуйте снова.'
  return error?.message || 'Что-то пошло не так.'
}
