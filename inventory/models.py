import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "pz", "Piezas"
        ML = "mL", "Mililitros"
        GRAM = "g", "Gramos"

    name = models.CharField("Nombre", max_length=180, unique=True)
    category = models.CharField("Categoria", max_length=80, default="Reactivo")
    unit = models.CharField("Unidad base", max_length=4, choices=Unit.choices)
    package_name = models.CharField("Presentacion", max_length=60, default="Caja")
    package_size = models.DecimalField("Contenido por presentacion", max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    minimum = models.DecimalField("Existencia minima", max_digits=14, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    requires_expiry = models.BooleanField("Requiere caducidad", default=True)
    days_after_opening = models.PositiveIntegerField("Dias utiles tras apertura", null=True, blank=True, validators=[MinValueValidator(1)])
    storage = models.CharField("Condiciones de almacenamiento", max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("operate_inventory", "Registrar entradas, aperturas y salidas"),
            ("manage_catalog", "Gestionar catalogo y bajas"),
            ("import_inventory", "Revisar y confirmar importaciones"),
        ]

    def __str__(self):
        return self.name


class Batch(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Aceptado"
        PENDING = "pending", "Pendiente de revision"
        QUARANTINE = "quarantine", "Cuarentena"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="batches")
    code = models.CharField("Lote", max_length=100)
    expiry = models.DateField("Caducidad del fabricante", null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACCEPTED)
    location = models.CharField("Ubicacion", max_length=120)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "code"], name="product_lot_unique")]

    def __str__(self):
        return f"{self.product} / {self.code}"


class Stock(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="stocks")
    receipt_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    initial = models.DecimalField(max_digits=14, decimal_places=3)
    balance = models.DecimalField(max_digits=14, decimal_places=3)
    opened_on = models.DateField(null=True, blank=True)
    opening_lifetime = models.PositiveIntegerField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(balance__gte=0), name="stock_nonnegative"),
            models.CheckConstraint(condition=models.Q(initial__gt=0), name="stock_initial_positive"),
            models.CheckConstraint(condition=models.Q(balance__lte=models.F("initial")), name="stock_not_over_capacity"),
        ]

    @property
    def effective_expiry(self):
        candidates = [self.batch.expiry]
        if self.opened_on and self.opening_lifetime:
            candidates.append(self.opened_on + timedelta(days=self.opening_lifetime))
        return min((value for value in candidates if value), default=None)

    @property
    def usable(self):
        return (
            self.balance > 0
            and self.batch.status == Batch.Status.ACCEPTED
            and (self.batch.expiry is not None or not self.batch.product.requires_expiry)
            and (self.effective_expiry is None or self.effective_expiry >= timezone.localdate())
        )

    @property
    def days_left(self):
        return (self.effective_expiry - timezone.localdate()).days if self.effective_expiry else None


class Movement(models.Model):
    class Kind(models.TextChoices):
        RECEIVE = "receive", "Entrada"
        USE = "use", "Consumo"
        OPEN = "open", "Apertura"
        DISPOSE = "dispose", "Baja"
        REVERSE = "reverse", "Reversion de salida"

    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    balance_after = models.DecimalField(max_digits=14, decimal_places=3)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=300)
    request_id = models.UUIDField(default=uuid.uuid4, unique=True)
    reverses = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]


class ImportFile(models.Model):
    name = models.CharField(max_length=200)
    digest = models.CharField(max_length=64, unique=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class ImportRow(models.Model):
    file = models.ForeignKey(ImportFile, on_delete=models.PROTECT, related_name="rows")
    sheet = models.CharField(max_length=80)
    row_number = models.PositiveIntegerField()
    original = models.JSONField()
    issues = models.JSONField(default=list)
    suggested_expiry = models.DateField(null=True)
    confirmed_at = models.DateTimeField(null=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, null=True, on_delete=models.PROTECT)
    excluded_at = models.DateTimeField(null=True)
    exclusion_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["file_id", "sheet", "row_number"]
        constraints = [models.UniqueConstraint(fields=["file", "sheet", "row_number"], name="source_row_unique")]


class Notification(models.Model):
    key = models.CharField(max_length=220, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    recipients = models.JSONField(default=list)
    state = models.CharField(max_length=15, default="pending", choices=[
        ("pending", "Pendiente"), ("sending", "En proceso"), ("accepted", "Aceptado por Microsoft"),
        ("failed", "Reintentable"), ("uncertain", "Resultado incierto"), ("cancelled", "Cancelado"),
    ])
    attempts = models.PositiveIntegerField(default=0)
    next_attempt = models.DateTimeField(default=timezone.now)
    detail = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MailConfiguration(models.Model):
    client_id = models.UUIDField("ID publico de aplicacion", null=True, blank=True)
    recipients = models.JSONField(default=list)
    enabled = models.BooleanField(default=False)


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    reference = models.CharField(max_length=180)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]