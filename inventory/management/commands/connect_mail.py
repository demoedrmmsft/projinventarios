from django.core.management.base import BaseCommand, CommandError

from inventory.mail import SCOPES, mail_client
from inventory.models import MailConfiguration


class Command(BaseCommand):
    help = "Autorizar personalmente una cuenta Microsoft; no solicita contrasena en esta aplicacion."

    def handle(self, *args, **options):
        configuration = MailConfiguration.objects.filter(pk=1).first()
        if not configuration or not configuration.client_id:
            raise CommandError("Guarde primero el ID publico en la pantalla de correo.")
        try:
            client = mail_client(configuration)
            flow = client.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise CommandError("Microsoft no inicio la autorizacion. Revise que la aplicacion admita cuentas personales y clientes publicos.")
            self.stdout.write(flow["message"])
            result = client.acquire_token_by_device_flow(flow)
        except (ValueError, OSError) as error:
            raise CommandError("No fue posible autorizar la cuenta. Revise el registro de aplicacion y la conexion.") from error
        if "access_token" not in result:
            raise CommandError("Autorizacion no completada. No se guardo ninguna contrasena.")
        accounts = client.get_accounts()
        current_id = result.get("id_token_claims", {}).get("oid")
        for account in accounts:
            if current_id and account.get("local_account_id") != current_id:
                client.remove_account(account)
        self.stdout.write(self.style.SUCCESS("Autorizacion guardada con proteccion de Windows. No se envio ningun correo."))