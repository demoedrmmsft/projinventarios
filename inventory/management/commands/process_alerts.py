from django.core.management.base import BaseCommand

from inventory.mail import generate_notifications, send_pending
from inventory.models import MailConfiguration


class Command(BaseCommand):
    help = "Generar alertas vigentes; enviar solo con --send y configuracion habilitada."

    def add_arguments(self, parser):
        parser.add_argument("--send", action="store_true")

    def handle(self, *args, **options):
        configuration = MailConfiguration.objects.filter(pk=1).first() or MailConfiguration()
        created = generate_notifications(configuration)
        sent = send_pending(configuration) if options["send"] else 0
        self.stdout.write(f"Nuevas alertas: {created}. Aceptadas por Microsoft: {sent}.")
        if not configuration.enabled:
            self.stdout.write("Correo deshabilitado; no se enviaron mensajes.")