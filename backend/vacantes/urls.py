from django.urls import path

from .views import VacantesView

urlpatterns = [path("", VacantesView.as_view(), name="vacantes")]
