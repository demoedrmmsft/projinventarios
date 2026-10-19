import csv
import uuid
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BatchStatusForm, MailForm, MovementForm, OpeningForm, ProductForm, ReceiveForm, ReverseForm, UploadForm
from .imports import stage_workbook
from .models import AuditEvent, Batch, ImportFile, ImportRow, MailConfiguration, Movement, Notification, Product, Stock
from .services import open_stock, ordered_stocks, receive, require, reverse, take


class LocalLoginView(LoginView):
    template_name = "registration/login.html"

    def dispatch(self, request, *args, **kwargs):
        if not get_user_model().objects.exists():
            return redirect("setup")
        return super().dispatch(request, *args, **kwargs)


def setup(request):
    if get_user_model().objects.exists():
        return redirect("login")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if get_user_model().objects.exists():
                return redirect("login")
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            call_command("setup_roles", verbosity=0)
            AuditEvent.objects.create(actor=user, action="Administrador inicial", reference=str(user.pk))
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/setup.html", {"form": form})


def page(request, rows, size=30):
    return Paginator(rows, size).get_page(request.GET.get("page"))


def problems(form, error):
    for message in error.messages:
        form.add_error(None, message)


@login_required
@permission_required("inventory.view_stock", raise_exception=True)
def dashboard(request):
    stocks = ordered_stocks()
    expired = [stock for stock in stocks if stock.days_left is not None and stock.days_left < 0]
    soon = [stock for stock in stocks if stock.usable and stock.days_left is not None and stock.days_left <= 90]
    usable = [stock for stock in stocks if stock.usable]
    totals = {}
    for stock in usable:
        totals[stock.batch.product_id] = totals.get(stock.batch.product_id, Decimal(0)) + stock.balance
    low = [product for product in Product.objects.filter(minimum__gt=0) if totals.get(product.pk, 0) < product.minimum]
    return render(request, "inventory/dashboard.html", {
        "active": "dashboard", "today": timezone.localdate(), "product_count": Product.objects.count(),
        "stock_count": len(usable), "expired_count": len(expired), "soon_count": len(soon),
        "pending_count": ImportRow.objects.filter(confirmed_at__isnull=True, excluded_at__isnull=True).count(),
        "attention": (expired + soon)[:10], "low": low, "movements": Movement.objects.select_related("actor", "stock__batch__product")[:6],
        "mail_pending": Notification.objects.exclude(state__in=["accepted", "cancelled"]).count(),
    })


@login_required
@permission_required("inventory.view_product", raise_exception=True)
def products(request):
    form = ProductForm(request.POST or None, initial={"name": request.GET.get("name", ""), "unit": "pz", "package_size": 100})
    if request.method == "POST":
        require(request.user, "manage_catalog")
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                AuditEvent.objects.create(actor=request.user, action="Alta de producto", reference=str(product.pk), detail={"name": product.name, "unit": product.unit, "package_size": str(product.package_size)})
            messages.success(request, "Producto registrado.")
            return redirect("products")
    rows = Product.objects.all()
    query = request.GET.get("q", "").strip()
    if query:
        rows = rows.filter(Q(name__icontains=query) | Q(category__icontains=query))
    return render(request, "inventory/products.html", {"active": "products", "rows": page(request, rows), "form": form, "q": query})


@login_required
@permission_required("inventory.view_stock", raise_exception=True)
def stock_list(request):
    rows = ordered_stocks()
    query = request.GET.get("q", "").strip()
    band = request.GET.get("state", "")
    if query:
        rows = [stock for stock in rows if query.casefold() in (stock.batch.product.name + " " + stock.batch.code + " " + stock.batch.location).casefold()]
    if band == "usable":
        rows = [stock for stock in rows if stock.usable]
    elif band == "expired":
        rows = [stock for stock in rows if stock.days_left is not None and stock.days_left < 0]
    elif band == "soon":
        rows = [stock for stock in rows if stock.usable and stock.days_left is not None and 0 <= stock.days_left <= 90]
    elif band == "blocked":
        rows = [stock for stock in rows if not stock.usable]
    return render(request, "inventory/stocks.html", {"active": "stocks", "rows": page(request, rows), "q": query, "state": band})


@login_required
@permission_required("inventory.operate_inventory", raise_exception=True)
def receive_stock(request, source_id=None):
    source = None
    initial = {"request_id": uuid.uuid4(), "packages": 1}
    if source_id:
        require(request.user, "import_inventory")
        source = get_object_or_404(ImportRow.objects.select_related("file"), pk=source_id)
        if source.confirmed_at or source.excluded_at:
            messages.info(request, "Esta fila ya tiene una resolucion registrada.")
            return redirect("import_detail", pk=source.file_id)
        if request.method == "POST" and request.POST.get("action") == "exclude":
            reason_form = ReverseForm(request.POST)
            if reason_form.is_valid():
                with transaction.atomic():
                    source = ImportRow.objects.select_for_update().get(pk=source.pk)
                    if source.confirmed_at or source.excluded_at:
                        return redirect("import_detail", pk=source.file_id)
                    source.excluded_at = timezone.now()
                    source.exclusion_reason = reason_form.cleaned_data["reason"]
                    source.save(update_fields=["excluded_at", "exclusion_reason"])
                    AuditEvent.objects.create(actor=request.user, action="Fila de Excel omitida", reference=str(source.pk), detail={"reason": source.exclusion_reason})
                messages.success(request, "Fila omitida con motivo; no se modificaron existencias.")
                return redirect("import_detail", pk=source.file_id)
            messages.error(request, "Indique un motivo para omitir la fila.")
        product = Product.objects.filter(name__iexact=source.original["product"]).first()
        initial.update(product=product, code="" if source.original.get("lot_is_date") else source.original["lot"], expiry=source.suggested_expiry)
    elif request.GET.get("product"):
        product = get_object_or_404(Product, pk=request.GET["product"])
        initial.update(product=product, content=product.package_size)
    form = ReceiveForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        count, content = values["packages"], values["content"]
        if values["product"].unit != "mL":
            count, content = 1, count * content
        try:
            stocks = receive(user=request.user, product=values["product"], code=values["code"], expiry=values["expiry"], location=values["location"],
                             containers=count, per_container=content, reason=values["reason"], request_id=values["request_id"], source=source)
        except ValidationError as error:
            problems(form, error)
        else:
            messages.success(request, "Entrada registrada y saldo actualizado.")
            return redirect("import_detail", pk=source.file_id) if source else redirect("stock_detail", pk=stocks[0].pk)
    return render(request, "inventory/receive.html", {"active": "imports" if source else "stocks", "form": form, "source": source,
                                                   "product_data": list(Product.objects.values("id", "package_size", "unit"))})


@login_required
@permission_required("inventory.view_stock", raise_exception=True)
def stock_detail(request, pk):
    stock = get_object_or_404(Stock.objects.select_related("batch__product"), pk=pk)
    movement_form, opening_form = MovementForm(), OpeningForm(prefix="opening")
    status_form = BatchStatusForm(initial={"status": stock.batch.status}, prefix="status")
    if request.method == "POST":
        action = request.POST.get("action")
        if action in {"use", "dispose"}:
            require(request.user, "manage_catalog" if action == "dispose" else "operate_inventory")
            movement_form = MovementForm(request.POST)
            if movement_form.is_valid():
                try:
                    take(user=request.user, stock_id=pk, dispose=action == "dispose", **movement_form.cleaned_data)
                except ValidationError as error:
                    problems(movement_form, error)
                else:
                    messages.success(request, "Salida registrada.")
                    return redirect("stock_detail", pk=pk)
        elif action == "open":
            require(request.user, "operate_inventory")
            opening_form = OpeningForm(request.POST, prefix="opening")
            if opening_form.is_valid():
                try:
                    open_stock(user=request.user, stock_id=pk, **opening_form.cleaned_data)
                except ValidationError as error:
                    problems(opening_form, error)
                else:
                    messages.success(request, "Apertura registrada.")
                    return redirect("stock_detail", pk=pk)
        elif action == "status":
            require(request.user, "manage_catalog")
            status_form = BatchStatusForm(request.POST, prefix="status")
            if status_form.is_valid():
                with transaction.atomic():
                    batch = Batch.objects.get(pk=stock.batch_id)
                    previous = batch.status
                    batch.status = status_form.cleaned_data["status"]
                    batch.save(update_fields=["status"])
                    AuditEvent.objects.create(actor=request.user, action="Estado de lote", reference=str(batch.pk),
                                              detail={"previous": previous, "new": batch.status, "reason": status_form.cleaned_data["reason"]})
                messages.success(request, "Estado del lote actualizado.")
                return redirect("stock_detail", pk=pk)
        else:
            return HttpResponse(status=400)
    return render(request, "inventory/stock_detail.html", {"active": "stocks", "stock": stock, "movement_form": movement_form,
                                                          "opening_form": opening_form, "status_form": status_form,
                                                          "movements": stock.movements.select_related("actor")})


@login_required
@permission_required("inventory.view_movement", raise_exception=True)
def movements(request):
    rows = Movement.objects.select_related("actor", "stock__batch__product")
    query = request.GET.get("q", "").strip()
    if query:
        rows = rows.filter(Q(stock__batch__product__name__icontains=query) | Q(stock__batch__code__icontains=query) | Q(actor__username__icontains=query))
    return render(request, "inventory/movements.html", {"active": "movements", "rows": page(request, rows), "q": query,
                                                       "events": AuditEvent.objects.select_related("actor")[:20]})


@login_required
@permission_required("inventory.manage_catalog", raise_exception=True)
def reverse_movement(request, pk):
    movement = get_object_or_404(Movement.objects.select_related("stock__batch__product"), pk=pk)
    form = ReverseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            reverse(user=request.user, movement_id=pk, **form.cleaned_data)
        except ValidationError as error:
            problems(form, error)
        else:
            messages.success(request, "Salida revertida con trazabilidad.")
            return redirect("stock_detail", pk=movement.stock_id)
    return render(request, "inventory/form.html", {"active": "movements", "title": "Revertir salida", "subtitle": str(movement.stock.batch), "form": form, "submit": "Confirmar reversion"})


@login_required
@permission_required("inventory.import_inventory", raise_exception=True)
def imports(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded = form.cleaned_data["file"]
        try:
            imported, created = stage_workbook(user=request.user, content=uploaded.read(), filename=uploaded.name)
        except ValidationError as error:
            problems(form, error)
        else:
            messages.success(request, "Libro preparado para revision; las existencias no cambiaron." if created else "Este libro ya fue revisado; se abrio el registro existente.")
            return redirect("import_detail", pk=imported.pk)
    return render(request, "inventory/imports.html", {"active": "imports", "form": form, "files": ImportFile.objects.order_by("-created_at")})


@login_required
@permission_required("inventory.import_inventory", raise_exception=True)
def import_detail(request, pk):
    imported = get_object_or_404(ImportFile, pk=pk)
    rows = imported.rows.all()
    query = request.GET.get("q", "").strip()
    if request.GET.get("pending") == "1":
        rows = rows.filter(confirmed_at__isnull=True, excluded_at__isnull=True)
    if query:
        rows = [row for row in rows if query.casefold() in row.original["product"].casefold()]
    return render(request, "inventory/import_detail.html", {"active": "imports", "file": imported, "rows": page(request, rows),
                                                           "pending": imported.rows.filter(confirmed_at__isnull=True, excluded_at__isnull=True).count(), "q": query})


@login_required
@permission_required("inventory.view_stock", raise_exception=True)
def alerts(request):
    stocks = [stock for stock in ordered_stocks() if stock.days_left is not None and stock.days_left <= 90]
    return render(request, "inventory/alerts.html", {"active": "alerts", "stocks": stocks, "notifications": Notification.objects.order_by("-created_at")[:30]})


@login_required
@permission_required("inventory.manage_catalog", raise_exception=True)
def mail_settings(request):
    configuration = MailConfiguration.objects.filter(pk=1).first() or MailConfiguration(pk=1)
    form = MailForm(request.POST or None, initial={"client_id": configuration.client_id, "recipients": "\n".join(configuration.recipients), "enabled": configuration.enabled})
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            configuration.client_id = form.cleaned_data["client_id"]
            configuration.recipients = form.cleaned_data["recipients"]
            configuration.enabled = form.cleaned_data["enabled"]
            configuration.save()
            AuditEvent.objects.create(actor=request.user, action="Configuracion de correo", reference="1", detail={"enabled": configuration.enabled, "recipients_count": len(configuration.recipients)})
        messages.success(request, "Configuracion guardada. La autorizacion Microsoft se realiza por separado.")
        return redirect("mail_settings")
    return render(request, "inventory/mail_settings.html", {"active": "alerts", "form": form, "enabled": configuration.enabled})


@login_required
@permission_required("inventory.view_movement", raise_exception=True)
def export_movements(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="movimientos.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Fecha CDMX", "Producto", "Lote", "Envase", "Movimiento", "Cantidad", "Unidad", "Saldo", "Responsable", "Motivo"])
    for movement in Movement.objects.select_related("actor", "stock__batch__product").iterator():
        values = [timezone.localtime(movement.created_at).isoformat(), movement.stock.batch.product.name, movement.stock.batch.code, movement.stock_id,
                  movement.get_kind_display(), movement.quantity, movement.stock.batch.product.unit, movement.balance_after, movement.actor.username, movement.reason]
        writer.writerow(["'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value for value in values])
    return response