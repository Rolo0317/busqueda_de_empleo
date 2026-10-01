from django.db.models import Avg, Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vacante

MAXIMO_POR_PAGINA = 100


class VacantesView(APIView):
    """Listado de vacantes con su resumen, para el panel."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        consulta = Vacante.objects.all()

        busqueda = request.query_params.get("q", "").strip()
        if busqueda:
            consulta = consulta.filter(
                Q(title__icontains=busqueda)
                | Q(company_name__icontains=busqueda)
                | Q(location__icontains=busqueda)
            )

        estado = request.query_params.get("estado", "").strip()
        if estado:
            consulta = consulta.filter(status=estado)

        if request.query_params.get("soloCalificadas") == "1":
            consulta = consulta.filter(match_score__gte=45)

        total = consulta.count()
        limite = min(int(request.query_params.get("limite", 25)), MAXIMO_POR_PAGINA)

        return Response({
            "total": total,
            "mostradas": min(total, limite),
            "resumen": self._resumen(),
            "vacantes": [self._serializar(v) for v in consulta[:limite]],
        })

    @staticmethod
    def _resumen() -> dict[str, object]:
        agregados = Vacante.objects.aggregate(
            total=Count("id"),
            aplicadas=Count("id", filter=Q(status="applied")),
            calificadas=Count("id", filter=Q(match_score__gte=45)),
            promedio=Avg("match_score"),
        )
        agregados["promedio"] = round(agregados["promedio"] or 0)
        return agregados

    @staticmethod
    def _serializar(v: Vacante) -> dict[str, object]:
        return {
            "id": v.id,
            "titulo": v.title,
            "empresa": v.company_name or "Confidencial",
            "ciudad": v.location or "",
            "salario": v.salary or "No especificado",
            "modalidad": v.modality or "",
            "score": v.match_score or 0,
            "estado": v.status or "",
            "plataforma": v.platform,
            "url": v.url,
        }
