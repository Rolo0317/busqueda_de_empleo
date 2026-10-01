from django.db import models


class Vacante(models.Model):
    """Mapea la tabla `jobs` que ya existe, escrita por el bot.

    managed = False: Django no la crea ni la migra, solo la lee. El duenio del
    esquema sigue siendo el bot.
    """

    platform = models.CharField(max_length=80)
    title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=300, null=True)
    salary = models.CharField(max_length=200, null=True)
    location = models.CharField(max_length=200, null=True)
    modality = models.CharField(max_length=120, null=True)
    published_at = models.CharField(max_length=120, null=True)
    url = models.CharField(max_length=1000)
    match_score = models.IntegerField(null=True)
    priority = models.CharField(max_length=40, null=True)
    status = models.CharField(max_length=40, null=True)
    first_seen_at = models.DateTimeField(null=True)
    last_seen_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = "jobs"
        ordering = ["-match_score", "-last_seen_at"]

    def __str__(self) -> str:
        return self.title
