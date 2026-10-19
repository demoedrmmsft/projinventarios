from datetime import timedelta

import msal
import requests
from django.conf import settings
from django.db.models import F
from django.utils import timezone
from msal_extensions import FilePersistenceWithDataProtection, PersistedTokenCache

from .models import MailConfiguration, Notification, Product
from .services import ordered_stocks

SCOPES = ["Mail.Send"]


def mail_client(configuration):
    if not configuration.client_id:
        raise ValueError("Falta el ID de aplicacion Microsoft.")
    persistence = FilePersistenceWithDataProtection(str(settings.DATA_DIR / "microsoft-cache.bin"))
    cache = PersistedTokenCache(persistence)
    return msal.PublicClientApplication(str(configuration.client_id), authority="https://login.microsoftonline.com/consumers", token_cache=cache)


def graph_send(configuration, notification):
    client = mail_client(configuration)
    accounts = client.get_accounts()
    if len(accounts) != 1:
        raise ValueError("Autorice una cuenta personal con el comando connect_mail.")
    token = client.acquire_token_silent(SCOPES, account=accounts[0])
    if not token or "access_token" not in token:
        raise ValueError("La autorizacion Microsoft vencio o fue revocada. Ejecute connect_mail.")
    return requests.post("https://graph.microsoft.com/v1.0/me/sendMail", headers={"Authorization": "Bearer " + token["access_token"]},
                         json={"message": {"subject": notification.subject, "body": {"contentType": "Text", "content": notification.body},
                                           "toRecipients": [{"emailAddress": {"address": recipient}} for recipient in notification.recipients]}}, timeout=(10, 35))


def current_alerts():
    alerts = {}
    totals = {}
    for stock in ordered_stocks():
        product = stock.batch.product
        if stock.usable:
            totals[product.pk] = totals.get(product.pk, 0) + stock.balance
        days = stock.days_left
        if stock.batch.status != "accepted" or days is None or days > 90:
            continue
        band = "vencido" if days < 0 else "30" if days <= 30 else "60" if days <= 60 else "90"
        key = f"expiry:{stock.pk}:{stock.effective_expiry.isoformat()}:{band}"
        subject = f"{'Vencido' if days < 0 else 'Caducidad ' + band + ' dias'}: {product.name}"
        body = (f"Producto: {product.name}\nLote: {stock.batch.code}\nEnvase/partida: {stock.pk}\n"
                f"Saldo: {stock.balance} {product.unit}\nCaducidad efectiva: {stock.effective_expiry.isoformat()}\n"
                f"Ubicacion: {stock.batch.location}\nDias restantes: {days}\nHorario: Ciudad de Mexico\n")
        alerts[key] = (subject[:200], body)
    for product in Product.objects.filter(minimum__gt=0):
        balance = totals.get(product.pk, 0)
        if balance < product.minimum:
            key = f"minimum:{product.pk}:{timezone.localdate().isoformat()}"
            alerts[key] = (f"Existencia minima: {product.name}"[:200], f"Producto: {product.name}\nSaldo util: {balance} {product.unit}\nMinimo: {product.minimum} {product.unit}")
    return alerts


def generate_notifications(configuration):
    active = current_alerts()
    Notification.objects.filter(state__in=["pending", "failed"]).exclude(key__in=active).update(state="cancelled", detail="La condicion de alerta dejo de estar activa.", updated_at=timezone.now())
    if not configuration.enabled or not configuration.recipients:
        return 0
    created_count = 0
    for key, (subject, body) in active.items():
        _, created = Notification.objects.get_or_create(key=key, defaults={"subject": subject, "body": body, "recipients": configuration.recipients})
        created_count += int(created)
    return created_count


def send_pending(configuration, limit=50):
    if not configuration.enabled or not configuration.client_id or not configuration.recipients:
        return 0
    now = timezone.now()
    Notification.objects.filter(state="sending", updated_at__lt=now - timedelta(minutes=15)).update(
        state="uncertain", detail="Proceso interrumpido. Revise Elementos enviados antes de resolver el estado.", updated_at=now)
    candidates = list(Notification.objects.filter(state__in=["pending", "failed"], next_attempt__lte=now).order_by("pk")[:limit])
    active = current_alerts()
    sent = 0
    for notification in candidates:
        if notification.key not in active:
            Notification.objects.filter(pk=notification.pk, state__in=["pending", "failed"]).update(state="cancelled", detail="Alerta ya no vigente.")
            continue
        claimed = Notification.objects.filter(pk=notification.pk, state__in=["pending", "failed"], next_attempt__lte=now).update(
            state="sending", attempts=F("attempts") + 1, updated_at=now)
        if not claimed:
            continue
        notification.refresh_from_db()
        next_delay = min(60 * 2 ** min(notification.attempts, 6), 3600)
        state, detail = "failed", ""
        try:
            response = graph_send(configuration, notification)
        except (ValueError, OSError, requests.RequestException) as error:
            if isinstance(error, requests.RequestException):
                state, detail = "uncertain", "Error de transporte durante el envio; no se reintenta automaticamente. Revise Elementos enviados."
            else:
                detail = "Autorizacion no disponible. Ejecute connect_mail con el usuario Windows de las tareas."
        else:
            if response.status_code == 202:
                state, detail = "accepted", "Microsoft acepto la solicitud; no confirma la entrega al destinatario."
                sent += 1
            elif response.status_code == 429 or response.status_code >= 500:
                detail = f"Microsoft HTTP {response.status_code}. Reintento programado."
                try:
                    next_delay = max(next_delay, int(response.headers.get("Retry-After", "0")))
                except ValueError:
                    pass
            else:
                state, detail = "cancelled", f"Microsoft HTTP {response.status_code}. Revise permisos/cuenta y configuracion."
        if state == "failed" and notification.attempts >= 5:
            state, detail = "cancelled", "Cinco intentos fallidos. Se requiere revisar la configuracion."
        Notification.objects.filter(pk=notification.pk, state="sending").update(
            state=state, detail=detail, next_attempt=now + timedelta(seconds=min(next_delay, 86400)), updated_at=timezone.now())
    return sent