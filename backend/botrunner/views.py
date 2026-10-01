from django.conf import settings
from rest_framework import status
from accounts.permissions import PasswordYaCambiada
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import BotNoDisponible, EjecucionEnCurso, RequiereSupervision, gestor


class EstadoBotView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(gestor.estado().como_dict())


class EjecutarBotView(APIView):
    """El boton de ejecutar. Requiere sesion: sin ella cualquiera dispararia
    postulaciones reales con la identidad del candidato."""

    permission_classes = [IsAuthenticated, PasswordYaCambiada]
    throttle_scope = "bot"

    def post(self, request: Request) -> Response:
        tope = settings.BOT_MAX_OFFERS
        solicitado = request.data.get("maxOfertas")
        if solicitado is not None:
            try:
                tope = min(int(solicitado), settings.BOT_MAX_OFFERS)
            except (TypeError, ValueError):
                return Response({"detail": "maxOfertas debe ser un numero."},
                                status=status.HTTP_400_BAD_REQUEST)
        if tope < 1:
            return Response({"detail": "maxOfertas debe ser al menos 1."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            estado = gestor.ejecutar(tope)
        except EjecucionEnCurso:
            return Response({"detail": "El bot ya esta corriendo."},
                            status=status.HTTP_409_CONFLICT)
        except RequiereSupervision:
            return Response(
                {"detail": "El bot esta en modo supervisado: cada postulacion se aprueba "
                           "por terminal. Ejecutalo con 'python main.py' o desactiva "
                           "SUPERVISED_APPLY cuando el flujo este verificado."},
                status=status.HTTP_409_CONFLICT,
            )
        except BotNoDisponible as error:
            return Response({"detail": str(error)},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(estado.como_dict(), status=status.HTTP_202_ACCEPTED)
