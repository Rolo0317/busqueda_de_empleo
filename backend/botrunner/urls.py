from django.urls import path

from .views import EjecutarBotView, EstadoBotView

urlpatterns = [
    path("run/", EjecutarBotView.as_view(), name="bot-run"),
    path("status/", EstadoBotView.as_view(), name="bot-status"),
]
