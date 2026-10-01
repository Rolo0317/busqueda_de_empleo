from django.contrib import admin

from .models import PerfilOperador


@admin.register(PerfilOperador)
class PerfilOperadorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "debe_cambiar_password", "creado")
    list_filter = ("debe_cambiar_password",)
