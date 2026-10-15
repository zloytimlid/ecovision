from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = "recognition"

router = SimpleRouter()
router.register("recognitions", views.RecognitionViewSet, basename="recognition")

urlpatterns = [
    path("recognize/", views.RecognizeView.as_view(), name="recognize"),
    path("health/", views.HealthView.as_view(), name="health"),
    *router.urls,
]
