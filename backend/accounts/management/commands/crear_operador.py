from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.claves import clave_temporal
from accounts.models import PerfilOperador


class Command(BaseCommand):
    help = "Crea la cuenta de operador con una clave temporal de un solo uso."

    def add_arguments(self, parser) -> None:
        parser.add_argument("usuario")
        parser.add_argument("--email", default="")
        parser.add_argument("--staff", action="store_true", help="Da acceso al admin de Django")

    def handle(self, *args, **opciones) -> None:
        Usuario = get_user_model()
        nombre = opciones["usuario"]

        if Usuario.objects.filter(username=nombre).exists():
            raise CommandError(f"El usuario '{nombre}' ya existe.")

        clave = clave_temporal()
        cuenta = Usuario.objects.create_user(
            username=nombre,
            email=opciones["email"],
            password=clave,
            is_staff=opciones["staff"],
            is_superuser=opciones["staff"],
        )
        PerfilOperador.objects.create(usuario=cuenta, debe_cambiar_password=True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"  Usuario:          {nombre}"))
        self.stdout.write(self.style.SUCCESS(f"  Clave temporal:   {clave}"))
        self.stdout.write("")
        self.stdout.write("  Debe cambiarse en el primer ingreso. Hasta entonces el bot")
        self.stdout.write("  no se puede ejecutar.")
        self.stdout.write("")
