"""Autenticacion por sesion. Se apoya en django.contrib.auth: hash, sesion y
rotacion de cookie ya estan resueltos y auditados alli."""
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

# Mismo mensaje para usuario inexistente y clave incorrecta: distinguirlos le
# confirma a un atacante que el usuario existe.
CREDENCIALES_INVALIDAS = {"detail": "Usuario o contraseña incorrectos."}


def _datos_sesion(cuenta) -> dict[str, object]:
    """Forma unica de la sesion: login, me y cambio de clave responden igual."""
    perfil = getattr(cuenta, "perfil_operador", None)
    return {
        "usuario": cuenta.get_username(),
        "debeCambiarPassword": perfil is not None and perfil.debe_cambiar_password,
    }


class CsrfView(APIView):
    """Entrega la cookie CSRF para que el frontend pueda enviar el token de vuelta."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request._request)})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request: Request) -> Response:
        usuario = str(request.data.get("usuario", "")).strip()
        password = str(request.data.get("password", ""))

        if not usuario or not password:
            return Response(CREDENCIALES_INVALIDAS, status=status.HTTP_400_BAD_REQUEST)

        cuenta = authenticate(request._request, username=usuario, password=password)
        if cuenta is None or not cuenta.is_active:
            return Response(CREDENCIALES_INVALIDAS, status=status.HTTP_401_UNAUTHORIZED)

        login(request._request, cuenta)
        return Response(_datos_sesion(cuenta))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Permite al frontend saber si la sesion sigue viva sin exponer nada mas."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(_datos_sesion(request.user))


class CambiarPasswordView(APIView):
    """Cambio de clave por el propio dueno de la cuenta."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        actual = str(request.data.get("actual", ""))
        nueva = str(request.data.get("nueva", ""))

        # Se exige la clave actual aunque haya sesion: una sesion robada no debe
        # poder dejar al dueno fuera de su propia cuenta.
        if not request.user.check_password(actual):
            return Response({"detail": "La contraseña actual no es correcta."},
                            status=status.HTTP_400_BAD_REQUEST)

        if nueva == actual:
            return Response({"detail": "La nueva contraseña debe ser distinta de la actual."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(nueva, request.user)
        except ValidationError as error:
            return Response({"detail": " ".join(error.messages)},
                            status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(nueva)
        request.user.save(update_fields=["password"])

        perfil = getattr(request.user, "perfil_operador", None)
        if perfil is not None and perfil.debe_cambiar_password:
            perfil.debe_cambiar_password = False
            perfil.save(update_fields=["debe_cambiar_password"])

        # Sin esto el cambio de clave cierra la sesion que acaba de usarse.
        update_session_auth_hash(request._request, request.user)

        return Response(_datos_sesion(request.user))
