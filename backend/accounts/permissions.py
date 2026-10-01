from rest_framework.permissions import BasePermission


class PasswordYaCambiada(BasePermission):
    """Bloquea la operacion mientras la clave temporal siga vigente.

    Sin esto la obligacion de cambiarla seria cosmetica: quien creo la cuenta
    todavia conoce la clave y podria disparar postulaciones reales.
    """

    message = "Debes cambiar tu contraseña temporal antes de usar el panel."

    def has_permission(self, request, view) -> bool:
        perfil = getattr(request.user, "perfil_operador", None)
        return perfil is None or not perfil.debe_cambiar_password
