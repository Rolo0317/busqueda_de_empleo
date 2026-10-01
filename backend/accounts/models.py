from django.conf import settings
from django.db import models


class PerfilOperador(models.Model):
    """Datos de operacion de la cuenta que no pertenecen al modelo User.

    Existe por una sola razon: una cuenta creada por otra persona nace con una
    clave que esa persona conoce, asi que no puede usarse hasta cambiarla.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_operador",
    )
    debe_cambiar_password = models.BooleanField(
        default=False,
        help_text="Obliga a cambiar la clave antes de usar el panel.",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "perfil de operador"
        verbose_name_plural = "perfiles de operador"

    def __str__(self) -> str:
        return f"{self.usuario.get_username()}"
