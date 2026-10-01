from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.claves import clave_temporal
from accounts.models import PerfilOperador


class Command(BaseCommand):
    help = "Asigna una clave temporal y obliga a cambiarla en el proximo ingreso."

    def add_arguments(self, parser) -> None:
        parser.add_argument("usuario")

    def handle(self, *args, **opciones) -> None:
        Usuario = get_user_model()
        nombre = opciones["usuario"]

        try:
            cuenta = Usuario.objects.get(username=nombre)
        except Usuario.DoesNotExist as error:
            raise CommandError(f"No existe el usuario '{nombre}'.") from error

        clave = clave_temporal()
        cuenta.set_password(clave)
        cuenta.save(update_fields=["password"])

        # La marca obliga a cambiarla y, mientras siga puesta, el bot no corre.
        perfil, _ = PerfilOperador.objects.get_or_create(usuario=cuenta)
        perfil.debe_cambiar_password = True
        perfil.save(update_fields=["debe_cambiar_password"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"  Usuario:         {nombre}"))
        self.stdout.write(self.style.SUCCESS(f"  Clave temporal:  {clave}"))
        self.stdout.write("")
        self.stdout.write("  Al entrar te pedira cambiarla. Las sesiones abiertas quedan invalidadas.")
        self.stdout.write("")
