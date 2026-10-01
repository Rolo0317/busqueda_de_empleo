from django.urls import path

from .views import CambiarPasswordView, CsrfView, LoginView, LogoutView, MeView

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("password/", CambiarPasswordView.as_view(), name="password"),
]
