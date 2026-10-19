from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crear roles Operador, Auditor y Responsable sin crear contrasenas."

    def handle(self, *args, **options):
        view_permissions = Permission.objects.filter(content_type__app_label="inventory", codename__startswith="view_")
        for name, custom in {
            "Auditor": [],
            "Operador": ["operate_inventory"],
            "Responsable": ["operate_inventory", "manage_catalog", "import_inventory"],
        }.items():
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(view_permissions | Permission.objects.filter(content_type__app_label="inventory", codename__in=custom))
        self.stdout.write(self.style.SUCCESS("Roles preparados. Asigne usuarios desde /admin/."))