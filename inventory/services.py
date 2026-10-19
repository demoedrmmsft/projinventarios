import uuid
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Batch, ImportRow, Movement, Product, Stock


def require(user, permission):
    if not user.is_active or not user.has_perm(f"inventory.{permission}"):
        raise PermissionDenied


def amount(value, product):
    try:
        quantity = Decimal(str(value))
        if not quantity.is_finite() or quantity <= 0 or quantity > Decimal("99999999999.999"):
            raise ValueError
        if quantity != quantity.quantize(Decimal("0.001")):
            raise ValueError
        if product.unit == Product.Unit.PIECE and quantity != quantity.to_integral_value():
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("Cantidad invalida: use valores positivos, hasta tres decimales; las piezas deben ser enteras.")
    return quantity


@transaction.atomic
def receive(*, user, product, code, expiry, location, containers, per_container, reason, request_id, source=None):
    require(user, "operate_inventory")
    if source:
        require(user, "import_inventory")
        source = ImportRow.objects.select_for_update().get(pk=source.pk)
        if source.confirmed_at:
            return list(source.batch.stocks.all())
        if source.excluded_at:
            raise ValidationError("La fila fue omitida con motivo documentado; no puede generar existencias.")
    quantity = amount(per_container, product)
    if not isinstance(containers, int) or not 1 <= containers <= 1000:
        raise ValidationError("Seleccione entre 1 y 1000 envases o partidas.")
    if not code.strip() or code.strip().upper() in {"S/L", "S/F"}:
        raise ValidationError("Confirme el lote real; para material sin lote use un identificador interno documentado.")
    if not location.strip() or not reason.strip():
        raise ValidationError("Indique ubicacion y motivo.")
    if product.requires_expiry and not expiry:
        raise ValidationError("Este producto requiere una caducidad verificada.")
    previous = Movement.objects.filter(request_id=request_id).first()
    if previous:
        prior_stocks = list(Stock.objects.select_related("batch").filter(receipt_id=request_id).order_by("pk"))
        if (previous.actor_id != user.pk or previous.kind != Movement.Kind.RECEIVE or not prior_stocks
                or len(prior_stocks) != containers or previous.stock.batch.product_id != product.pk
                or previous.stock.batch.code != code.strip() or previous.stock.batch.expiry != expiry
                or previous.stock.batch.location != location.strip() or previous.quantity != quantity):
            raise ValidationError("La solicitud ya se utilizo para una entrada diferente.")
        return prior_stocks
    batch, created = Batch.objects.get_or_create(product=product, code=code.strip(), defaults={"expiry": expiry, "location": location.strip()})
    if not created and (batch.expiry != expiry or batch.location != location.strip()):
        raise ValidationError("El lote ya existe con otra caducidad o ubicacion. Revise el registro antes de continuar.")
    if source and not created and batch.stocks.exists():
        raise ValidationError("Ya hay existencias para este producto/lote. Concilie el saldo para evitar duplicar la importacion.")
    stocks = []
    for position in range(containers):
        stock = Stock.objects.create(batch=batch, receipt_id=request_id, initial=quantity, balance=quantity, opening_lifetime=product.days_after_opening)
        Movement.objects.create(stock=stock, kind=Movement.Kind.RECEIVE, quantity=quantity, balance_after=quantity,
                                actor=user, reason=reason.strip(), request_id=request_id if position == 0 else uuid.uuid4())
        stocks.append(stock)
    if source:
        source.confirmed_at = timezone.now()
        source.confirmed_by = user
        source.batch = batch
        source.save(update_fields=["confirmed_at", "confirmed_by", "batch"])
    return stocks


@transaction.atomic
def take(*, user, stock_id, quantity, reason, request_id, dispose=False):
    require(user, "manage_catalog" if dispose else "operate_inventory")
    stock = Stock.objects.select_related("batch__product").get(pk=stock_id)
    quantity = amount(quantity, stock.batch.product)
    previous = Movement.objects.filter(request_id=request_id).first()
    if previous:
        if previous.stock_id != stock.pk or previous.quantity != -quantity or previous.actor_id != user.pk:
            raise ValidationError("La solicitud ya se utilizo para otro movimiento.")
        return previous
    if not reason.strip():
        raise ValidationError("Especifique el motivo o destino de la salida.")
    if not dispose and not stock.usable:
        raise ValidationError("No se puede consumir material vencido, bloqueado, sin caducidad requerida o agotado.")
    if not dispose and stock.batch.product.days_after_opening and not stock.opened_on:
        raise ValidationError("Registre la apertura del envase antes del primer consumo.")
    if quantity > stock.balance:
        raise ValidationError("La salida supera la existencia disponible.")
    new_balance = stock.balance - quantity
    updated = Stock.objects.filter(pk=stock.pk, version=stock.version).update(balance=new_balance, version=stock.version + 1)
    if updated != 1:
        raise ValidationError("La existencia cambio. Actualice y vuelva a intentar.")
    return Movement.objects.create(stock=stock, kind=Movement.Kind.DISPOSE if dispose else Movement.Kind.USE,
                                   quantity=-quantity, balance_after=new_balance, actor=user, reason=reason.strip(), request_id=request_id)


@transaction.atomic
def open_stock(*, user, stock_id, opened_on, request_id):
    require(user, "operate_inventory")
    stock = Stock.objects.select_related("batch__product").get(pk=stock_id)
    if Movement.objects.filter(request_id=request_id, stock=stock, kind=Movement.Kind.OPEN).exists():
        return stock
    if stock.opened_on:
        raise ValidationError("El envase ya tiene una apertura registrada.")
    if not stock.usable or opened_on > timezone.localdate():
        raise ValidationError("No es posible abrir este envase o la fecha es futura.")
    stock.opened_on = opened_on
    stock.version += 1
    stock.save(update_fields=["opened_on", "version"])
    Movement.objects.create(stock=stock, kind=Movement.Kind.OPEN, quantity=0, balance_after=stock.balance,
                            actor=user, reason=f"Apertura: {opened_on.isoformat()}", request_id=request_id)
    return stock


@transaction.atomic
def reverse(*, user, movement_id, reason, request_id):
    require(user, "manage_catalog")
    original = Movement.objects.select_related("stock__batch__product").get(pk=movement_id)
    if original.kind not in {Movement.Kind.USE, Movement.Kind.DISPOSE}:
        raise ValidationError("Solo se revierten consumos o bajas. Los registros originales no se borran.")
    if Movement.objects.filter(reverses=original).exists():
        raise ValidationError("Esta salida ya fue revertida.")
    if not reason.strip():
        raise ValidationError("Documente el motivo de la reversion.")
    stock = original.stock
    new_balance = stock.balance - original.quantity
    if new_balance > stock.initial:
        raise ValidationError("La reversion excede el contenido recibido.")
    stock.balance = new_balance
    stock.version += 1
    stock.save(update_fields=["balance", "version"])
    return Movement.objects.create(stock=stock, kind=Movement.Kind.REVERSE, quantity=-original.quantity,
                                   balance_after=new_balance, actor=user, reason=reason.strip(), request_id=request_id, reverses=original)


def ordered_stocks():
    stocks = list(Stock.objects.select_related("batch__product").filter(balance__gt=0))
    return sorted(stocks, key=lambda stock: (not stock.usable, stock.effective_expiry or timezone.datetime.max.date(), stock.received_at, stock.pk))