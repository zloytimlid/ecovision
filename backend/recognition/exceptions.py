from django.conf import settings

from config.exceptions import ApiError


class InvalidImageError(ApiError):
    status_code = 400
    default_code = "invalid_image"
    default_detail = "Файл не является изображением. Поддерживаются JPEG, PNG и WEBP."


class MissingClientIdError(ApiError):
    status_code = 400
    default_code = "missing_client_id"
    default_detail = "Не передан или неверен идентификатор устройства (X-Client-Id)."


class FileTooLargeError(ApiError):
    status_code = 413
    default_code = "file_too_large"

    def __init__(self):
        super().__init__(f"Файл больше {settings.MAX_UPLOAD_MB} МБ.")


class ModelUnavailableError(ApiError):
    status_code = 502
    default_code = "model_unavailable"
    default_detail = "Сервис распознавания временно недоступен. Попробуйте позже."


class ModelTimeoutError(ApiError):
    status_code = 504
    default_code = "model_timeout"
    default_detail = "Сервис распознавания не ответил вовремя. Попробуйте ещё раз."
