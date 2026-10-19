from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from inventory.backup import create_backup


class Command(BaseCommand):
    help = "Respaldar SQLite y clave local, verificando integridad de una copia extraida."

    def handle(self, *args, **options):
        destination = settings.BASE_DIR / "backups" / f"inventario-{timezone.now().strftime('%Y%m%d-%H%M%S-%f')}.zip"
        try:
            create_backup(settings.DATABASES["default"]["NAME"], settings.DATA_DIR / "secret.key", destination)
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Respaldo verificado: {destination}"))