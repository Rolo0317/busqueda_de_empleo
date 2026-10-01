from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/bot/", include("botrunner.urls")),
    path("api/vacantes/", include("vacantes.urls")),
]
