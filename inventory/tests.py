import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Batch, Movement, Product, Stock
from .services import open_stock, ordered_stocks, receive, reverse, take


class InventoryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "", "test-password-only")
        self.product = Product.objects.create(name="Reactivo", unit="mL", package_size=500)

    def receive(self, **changes):
        values = dict(user=self.user, product=self.product, code="LOT-1", expiry=timezone.localdate() + timedelta(days=60),
                      location="Estante A", containers=1, per_container=500, reason="Recepcion verificada", request_id=uuid.uuid4())
        values.update(changes)
        return receive(**values)

    def take(self, stock, **changes):
        values = dict(user=self.user, stock_id=stock.pk, quantity="12.5", reason="Analisis", request_id=uuid.uuid4())
        values.update(changes)
        return take(**values)

    def test_decimal_consumption_and_audit(self):
        stock = self.receive()[0]
        self.take(stock)
        stock.refresh_from_db()
        self.assertEqual(stock.balance, Decimal("487.500"))
        self.assertEqual(stock.movements.count(), 2)

    def test_negative_balance_blocked(self):
        stock = self.receive()[0]
        with self.assertRaises(ValidationError):
            self.take(stock, quantity=501)
        stock.refresh_from_db()
        self.assertEqual(stock.balance, 500)

    def test_expiry_checked_on_every_consumption(self):
        stock = self.receive(expiry=timezone.localdate() - timedelta(days=1))[0]
        with self.assertRaises(ValidationError):
            self.take(stock)
        self.take(stock, dispose=True)

    def test_valid_until_end_of_expiry_day(self):
        stock = self.receive(expiry=timezone.localdate())[0]
        self.take(stock)

    def test_opening_does_not_consume_and_limits_expiry(self):
        self.product.days_after_opening = 7
        self.product.save()
        stock = self.receive()[0]
        with self.assertRaises(ValidationError):
            self.take(stock)
        stock = open_stock(user=self.user, stock_id=stock.pk, opened_on=timezone.localdate(), request_id=uuid.uuid4())
        self.assertEqual(stock.balance, 500)
        self.assertEqual(stock.effective_expiry, timezone.localdate() + timedelta(days=7))
        self.take(stock)

    def test_whole_pieces_only(self):
        self.product.unit = "pz"
        self.product.save()
        stock = self.receive()[0]
        with self.assertRaises(ValidationError):
            self.take(stock, quantity="0.5")

    def test_double_submit_is_idempotent(self):
        stock = self.receive()[0]
        request_id = uuid.uuid4()
        self.take(stock, request_id=request_id)
        self.take(stock, request_id=request_id)
        stock.refresh_from_db()
        self.assertEqual(stock.balance, Decimal("487.5"))

    def test_receipt_retry_keeps_all_containers_and_checks_payload(self):
        request_id = uuid.uuid4()
        first = self.receive(request_id=request_id, containers=5)
        second = self.receive(request_id=request_id, containers=5)
        self.assertEqual([stock.pk for stock in first], [stock.pk for stock in second])
        with self.assertRaises(ValidationError):
            self.receive(request_id=request_id, containers=2)

    def test_auditor_cannot_mutate(self):
        stock = self.receive()[0]
        user = get_user_model().objects.create_user("auditor")
        with self.assertRaises(PermissionDenied):
            self.take(stock, user=user)

    def test_lot_expiry_conflict_not_merged(self):
        self.receive()
        with self.assertRaises(ValidationError):
            self.receive(expiry=timezone.localdate() + timedelta(days=90))
        self.assertEqual(Stock.objects.count(), 1)

    def test_fefo(self):
        later = self.receive()[0]
        earlier = self.receive(code="LOT-2", expiry=timezone.localdate() + timedelta(days=10))[0]
        self.assertEqual([stock.pk for stock in ordered_stocks()], [earlier.pk, later.pk])

    def test_reversal_keeps_original_movement(self):
        stock = self.receive()[0]
        movement = self.take(stock)
        reverse(user=self.user, movement_id=movement.pk, reason="Error de captura", request_id=uuid.uuid4())
        stock.refresh_from_db()
        self.assertEqual(stock.balance, 500)
        self.assertTrue(Movement.objects.filter(pk=movement.pk).exists())
        with self.assertRaises(ValidationError):
            reverse(user=self.user, movement_id=movement.pk, reason="Otra vez", request_id=uuid.uuid4())


class ImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("importer", "", "test-password-only")

    def workbook(self):
        from datetime import datetime
        from io import BytesIO
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "INVENTARIO REACTIVOS"
        sheet.append(["NOMBRE DEL PRODUCTO", "LOTE", "CAJAS", "FECHA CADUCIDAD"])
        sheet.append(["COLESTEROL", "00123", "=2-SUMIF(I:I,B2,J:J)", datetime(2027, 6, 12)])
        sheet.append(["COLESTEROL", "00123", 2, "09/10/206"])
        stream = BytesIO()
        workbook.save(stream)
        return stream.getvalue()

    def test_staging_preserves_source_without_stock(self):
        from .imports import stage_workbook

        imported, created = stage_workbook(user=self.user, content=self.workbook(), filename="inventario.xlsx")
        self.assertTrue(created)
        self.assertEqual(imported.rows.count(), 2)
        row = imported.rows.first()
        self.assertEqual(row.original["lot"], "00123")
        self.assertIn("=2-SUMIF", row.original["quantities"]["CAJAS"]["raw"])
        self.assertTrue(any("repetido" in issue for issue in row.issues))
        self.assertFalse(Stock.objects.exists())

    def test_same_file_does_not_duplicate_rows(self):
        from .imports import stage_workbook

        content = self.workbook()
        first, _ = stage_workbook(user=self.user, content=content, filename="one.xlsx")
        second, created = stage_workbook(user=self.user, content=content, filename="two.xlsx")
        self.assertFalse(created)
        self.assertEqual(first.pk, second.pk)

    def test_dates_are_not_guessed(self):
        from datetime import date
        from openpyxl.utils.datetime import WINDOWS_EPOCH
        from .imports import suggest_date

        for value in ["09/10/206", "12/062026", "08/01/20227", "06/07/2026", "S/F", 11355]:
            self.assertIsNone(suggest_date(value, WINDOWS_EPOCH)[0])
        self.assertEqual(suggest_date("3/27/2026", WINDOWS_EPOCH)[0], date(2026, 3, 27))

    def test_import_confirmation_is_idempotent(self):
        from .imports import stage_workbook

        imported, _ = stage_workbook(user=self.user, content=self.workbook(), filename="test.xlsx")
        product = Product.objects.create(name="COLESTEROL", unit="mL", package_size=500)
        values = dict(user=self.user, product=product, code="00123", expiry=timezone.localdate() + timedelta(days=60),
                      location="A", containers=1, per_container=500, reason="Saldo verificado", request_id=uuid.uuid4(), source=imported.rows.first())
        receive(**values)
        receive(**values)
        self.assertEqual(Stock.objects.count(), 1)

    def test_different_file_cannot_reimport_existing_lot(self):
        from .imports import stage_workbook

        imported, _ = stage_workbook(user=self.user, content=self.workbook(), filename="test.xlsx")
        product = Product.objects.create(name="COLESTEROL", unit="mL", package_size=500)
        values = dict(user=self.user, product=product, code="00123", expiry=timezone.localdate() + timedelta(days=60),
                      location="A", containers=1, per_container=500, reason="Saldo verificado", request_id=uuid.uuid4())
        receive(**values)
        with self.assertRaises(ValidationError):
            receive(**{**values, "request_id": uuid.uuid4(), "source": imported.rows.first()})


class ScreenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("screen-admin", "", "test-password-only")
        cls.product = Product.objects.create(name="Reactivo de prueba", unit="mL", package_size=500)
        cls.stock = receive(user=cls.user, product=cls.product, code="A001", expiry=timezone.localdate() + timedelta(days=15),
                            location="Estante A", containers=1, per_container=500, reason="Prueba", request_id=uuid.uuid4())[0]

    def test_login_required(self):
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_all_primary_screens_render(self):
        self.client.force_login(self.user)
        for url in ["/", "/products/", "/stocks/", f"/stocks/{self.stock.pk}/", "/stocks/new/", "/movements/", "/imports/", "/alerts/", "/movements/export/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_stock_forms_have_unique_element_ids(self):
        from html.parser import HTMLParser

        class IdParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []

            def handle_starttag(self, tag, attrs):
                self.ids.extend(value for key, value in attrs if key == "id")

        self.client.force_login(self.user)
        parser = IdParser()
        parser.feed(self.client.get(f"/stocks/{self.stock.pk}/").content.decode())
        self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_prefixed_opening_and_quarantine_forms(self):
        self.client.force_login(self.user)
        response = self.client.post(f"/stocks/{self.stock.pk}/", {"action": "open", "opening-opened_on": timezone.localdate().isoformat(), "opening-request_id": uuid.uuid4()})
        self.assertEqual(response.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.opened_on, timezone.localdate())
        response = self.client.post(f"/stocks/{self.stock.pk}/", {"action": "status", "status-status": "quarantine", "status-reason": "Inspeccion"})
        self.assertEqual(response.status_code, 302)
        self.stock.batch.refresh_from_db()
        self.assertEqual(self.stock.batch.status, "quarantine")

    def test_receipt_boxes_convert_to_pieces(self):
        self.client.force_login(self.user)
        product = Product.objects.create(name="Gasa", unit="pz", package_size=100)
        response = self.client.post("/stocks/new/", {"product": product.pk, "code": "G001", "expiry": "2027-12-31", "location": "A", "packages": 5, "content": 100,
                                                   "reason": "Recepcion verificada", "verified": "on", "request_id": uuid.uuid4()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Stock.objects.get(batch__product=product).balance, 500)

    def test_five_liquid_containers_keep_separate_balances(self):
        self.client.force_login(self.user)
        response = self.client.post("/stocks/new/", {"product": self.product.pk, "code": "M002", "expiry": "2027-12-31", "location": "A", "packages": 5, "content": 100,
                                                   "reason": "Recepcion verificada", "verified": "on", "request_id": uuid.uuid4()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Stock.objects.filter(batch__code="M002").count(), 5)

    def test_no_mutations_by_get_or_without_permission(self):
        from django.contrib.auth.models import Permission

        auditor = get_user_model().objects.create_user("readonly")
        auditor.user_permissions.add(*Permission.objects.filter(codename__in=["view_stock", "view_product", "view_movement"]))
        self.client.force_login(auditor)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/stocks/new/").status_code, 403)
        self.assertEqual(self.client.post(f"/stocks/{self.stock.pk}/", {"action": "use"}).status_code, 403)
        self.assertEqual(self.client.post("/products/", {"name": "Unauthorized"}).status_code, 403)
        self.assertEqual(self.client.get("/stocks/", {"action": "use"}).status_code, 200)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.balance, 500)

    def test_post_requires_csrf(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(f"/stocks/{self.stock.pk}/", {"action": "use"}).status_code, 403)

    def test_initial_setup_cannot_be_reopened(self):
        response = self.client.get("/setup/")
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)

    def test_import_review_and_confirmation_screens(self):
        from .imports import stage_workbook

        self.client.force_login(self.user)
        imported, _ = stage_workbook(user=self.user, content=ImportTests().workbook(), filename="test.xlsx")
        self.assertEqual(self.client.get(f"/imports/{imported.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/imports/rows/{imported.rows.first().pk}/").status_code, 200)

    def test_excluding_duplicate_row_is_audited_without_stock(self):
        from .imports import stage_workbook
        from .models import AuditEvent

        self.client.force_login(self.user)
        imported, _ = stage_workbook(user=self.user, content=ImportTests().workbook(), filename="test.xlsx")
        row = imported.rows.first()
        before = Stock.objects.count()
        response = self.client.post(f"/imports/rows/{row.pk}/", {"action": "exclude", "reason": "Duplicado conciliado en fila 3", "request_id": uuid.uuid4()})
        self.assertEqual(response.status_code, 302)
        row.refresh_from_db()
        self.assertIsNotNone(row.excluded_at)
        self.assertEqual(Stock.objects.count(), before)
        self.assertTrue(AuditEvent.objects.filter(action="Fila de Excel omitida").exists())
        with self.assertRaises(ValidationError):
            receive(user=self.user, product=self.product, code="Excluded", expiry=timezone.localdate(), location="A", containers=1,
                    per_container=500, reason="Prueba", request_id=uuid.uuid4(), source=row)


class SetupTests(TestCase):
    def test_initial_admin_created_once(self):
        self.assertRedirects(self.client.get("/accounts/login/"), "/setup/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/setup/").status_code, 200)
        response = self.client.post("/setup/", {"username": "lab-owner", "password1": "Initial-test-only-7539!", "password2": "Initial-test-only-7539!"})
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="lab-owner")
        self.assertTrue(user.is_superuser)
        self.assertNotEqual(user.password, "Initial-test-only-7539!")
        response = self.client.post("/setup/", {"username": "other", "password1": "Other-test-7539!", "password2": "Other-test-7539!"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), 1)


class NotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("notifier", "", "test-password-only")
        cls.product = Product.objects.create(name="Reactivo alerta", unit="mL", package_size=500)
        cls.stock = receive(user=cls.user, product=cls.product, code="AL1", expiry=timezone.localdate() + timedelta(days=20),
                            location="A", containers=1, per_container=500, reason="Prueba", request_id=uuid.uuid4())[0]

    def configuration(self):
        from .models import MailConfiguration

        return MailConfiguration(client_id=uuid.uuid4(), recipients=["test@example.com"], enabled=True)

    def test_highest_band_and_deduplication(self):
        from .mail import generate_notifications
        from .models import Notification

        configuration = self.configuration()
        self.assertEqual(generate_notifications(configuration), 1)
        self.assertEqual(generate_notifications(configuration), 0)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertTrue(Notification.objects.get().key.endswith(":30"))

    def test_depleted_stock_cancels_pending_notification(self):
        from .mail import generate_notifications
        from .models import Notification

        configuration = self.configuration()
        generate_notifications(configuration)
        take(user=self.user, stock_id=self.stock.pk, quantity=500, reason="Prueba", request_id=uuid.uuid4())
        generate_notifications(configuration)
        self.assertEqual(Notification.objects.get().state, "cancelled")

    def test_acceptance_is_not_delivery_and_not_resent(self):
        from unittest.mock import Mock, patch
        from .mail import generate_notifications, send_pending
        from .models import Notification

        configuration = self.configuration()
        generate_notifications(configuration)
        with patch("inventory.mail.graph_send", return_value=Mock(status_code=202)) as send:
            self.assertEqual(send_pending(configuration), 1)
            self.assertEqual(send_pending(configuration), 0)
            self.assertEqual(send.call_count, 1)
        self.assertEqual(Notification.objects.get().state, "accepted")

    def test_timeout_not_retried_as_if_unsent(self):
        import requests
        from unittest.mock import patch
        from .mail import generate_notifications, send_pending
        from .models import Notification

        configuration = self.configuration()
        generate_notifications(configuration)
        with patch("inventory.mail.graph_send", side_effect=requests.Timeout):
            send_pending(configuration)
        self.assertEqual(Notification.objects.get().state, "uncertain")

    def test_throttling_respects_retry_after(self):
        from unittest.mock import Mock, patch
        from .mail import generate_notifications, send_pending
        from .models import Notification

        configuration = self.configuration()
        generate_notifications(configuration)
        with patch("inventory.mail.graph_send", return_value=Mock(status_code=429, headers={"Retry-After": "600"})):
            send_pending(configuration)
        notification = Notification.objects.get()
        self.assertEqual(notification.state, "failed")
        self.assertGreater(notification.next_attempt, timezone.now() + timedelta(minutes=9))

    def test_disabled_mail_never_sends(self):
        from unittest.mock import patch
        from .mail import generate_notifications, send_pending

        configuration = self.configuration()
        configuration.enabled = False
        with patch("inventory.mail.graph_send") as send:
            self.assertEqual(generate_notifications(configuration), 0)
            self.assertEqual(send_pending(configuration), 0)
            send.assert_not_called()

    def test_mail_configuration_screen(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/settings/mail/").status_code, 200)
        response = self.client.post("/settings/mail/", {"client_id": uuid.uuid4(), "recipients": "test@example.com\nother@example.com", "enabled": "on"})
        self.assertEqual(response.status_code, 302)


class BackupTests(TestCase):
    def test_backup_can_be_extracted_and_read(self):
        import sqlite3
        import tempfile
        from contextlib import closing
        from pathlib import Path
        from zipfile import ZipFile
        from .backup import create_backup

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "source.sqlite3"
            with closing(sqlite3.connect(database)) as source, source:
                source.execute("CREATE TABLE sample (quantity TEXT)")
                source.execute("INSERT INTO sample VALUES (?)", ("487.500",))
            secret = root / "secret.key"
            secret.write_text("temporary-test-key", encoding="ascii")
            destination = create_backup(database, secret, root / "backup.zip")
            with ZipFile(destination) as archive:
                restored = root / "check.sqlite3"
                restored.write_bytes(archive.read("inventory.sqlite3"))
            with closing(sqlite3.connect(restored)) as connection:
                self.assertEqual(connection.execute("SELECT quantity FROM sample").fetchone()[0], "487.500")