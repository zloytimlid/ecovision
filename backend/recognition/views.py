import logging
import time

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .client_id import get_client_id
from .exceptions import (
    FileTooLargeError,
    InvalidImageError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from .models import DetectedObject, Recognition
from .serializers import FeedbackSerializer, RecognitionListSerializer, RecognitionSerializer
from .services.image_utils import InvalidImage, process_image
from .services.postprocess import analyze, load_mapping, normalize
from .services.roboflow_client import RoboflowClient, RoboflowError, RoboflowTimeout
from .throttling import RecognizeRateThrottle

logger = logging.getLogger(__name__)


def recognition_queryset():
    return Recognition.objects.select_related("category", "feedback").prefetch_related(
        "detected_objects__category"
    )


class RecognitionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """History of the current client: only records with its own X-Client-Id are visible."""

    def get_queryset(self):
        return recognition_queryset().filter(client_id=get_client_id(self.request))

    def get_serializer_class(self):
        return RecognitionListSerializer if self.action == "list" else RecognitionSerializer

    @action(detail=True, methods=["post"])
    def feedback(self, request, pk=None):
        recognition = self.get_object()
        serializer = FeedbackSerializer(
            instance=getattr(recognition, "feedback", None), data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(recognition=recognition)
        return Response(serializer.data)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "model_configured": RoboflowClient().is_configured})


class RecognizeView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [RecognizeRateThrottle]

    def post(self, request):
        client_id = get_client_id(request)

        upload = request.FILES.get("image")
        if upload is None:
            raise InvalidImageError("Прикрепите фото в поле image.")
        if upload.size > settings.MAX_UPLOAD_BYTES:
            raise FileTooLargeError()
        try:
            image = process_image(upload.read())
        except InvalidImage as exc:
            logger.info("Rejected upload %r: %s", upload.name, exc)
            raise InvalidImageError() from None

        started = time.monotonic()
        try:
            raw = RoboflowClient().predict(image.content)
        except RoboflowTimeout:
            raise ModelTimeoutError() from None
        except RoboflowError:
            raise ModelUnavailableError() from None
        inference_ms = round((time.monotonic() - started) * 1000)

        mapping = load_mapping()
        analysis = analyze(
            normalize(raw, settings.ROBOFLOW_MODEL_TYPE),
            mapping,
            model_type=settings.ROBOFLOW_MODEL_TYPE,
            min_confidence=settings.ROBOFLOW_MIN_CONFIDENCE,
            low_confidence_threshold=settings.LOW_CONFIDENCE_THRESHOLD,
        )
        logger.info(
            "Recognition: status=%s class=%s inference=%dms",
            analysis.status,
            analysis.top["model_class"] if analysis.top else None,
            inference_ms,
        )

        recognition = self._save(client_id, image, raw, inference_ms, analysis)
        serializer = RecognitionSerializer(
            recognition_queryset().get(pk=recognition.pk),
            context={"request": request, "mapping": mapping},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _save(client_id, image, raw, inference_ms, analysis):
        recognition = Recognition(
            client_id=client_id,
            image_width=image.width,
            image_height=image.height,
            status=analysis.status,
            top_class=analysis.top["model_class"] if analysis.top else None,
            top_confidence=analysis.top["confidence"] if analysis.top else None,
            category=analysis.category,
            raw_response=raw,
            inference_ms=inference_ms,
        )
        recognition.image.save(f"{recognition.id.hex}.jpg", ContentFile(image.content), save=False)
        try:
            with transaction.atomic():
                recognition.save()
                DetectedObject.objects.bulk_create(
                    DetectedObject(
                        recognition=recognition,
                        model_class=obj["model_class"],
                        confidence=obj["confidence"],
                        category=obj["category"],
                        **obj["bbox"],
                    )
                    for obj in analysis.objects
                )
        except Exception:
            recognition.image.delete(save=False)
            raise
        return recognition
