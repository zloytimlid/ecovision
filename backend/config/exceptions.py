"""Unified API error format: {"error": {"code": "...", "message": "..."}}."""

from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler


class ApiError(exceptions.APIException):
    """Base class for API errors with a stable machine-readable code."""

    status_code = 400
    default_code = "error"
    default_detail = "Ошибка запроса."


def _first_message(data):
    if isinstance(data, dict):
        for value in data.values():
            return _first_message(value)
    if isinstance(data, (list, tuple)) and data:
        return _first_message(data[0])
    return str(data) if data else "Некорректные данные."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = None
    if isinstance(exc, (Http404, exceptions.NotFound)):
        code, message = "not_found", "Запись не найдена."
    elif isinstance(exc, exceptions.Throttled):
        code = "throttled"
        message = "Слишком много запросов. Попробуйте чуть позже."
        if exc.wait:
            message = f"Слишком много запросов. Повторите через {int(exc.wait) + 1} с."
    elif isinstance(exc, exceptions.ValidationError):
        code, message, details = "validation_error", _first_message(exc.detail), exc.detail
    else:
        code = getattr(exc.detail, "code", None) or exc.default_code
        message = str(exc.detail)

    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    response.data = {"error": error}
    return response
