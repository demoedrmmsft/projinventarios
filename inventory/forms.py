import uuid
from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Batch, Product
from .services import amount


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "unit", "package_name", "package_size", "minimum", "requires_expiry", "days_after_opening", "storage"]
        widgets = {"storage": forms.Textarea(attrs={"rows": 2})}

    def clean(self):
        values = super().clean()
        if values.get("unit") == "pz":
            for field in ["package_size", "minimum"]:
                value = values.get(field)
                if value is not None and value != value.to_integral_value():
                    self.add_error(field, "Para piezas use numeros enteros.")
        return values


class ReceiveForm(forms.Form):
    product = forms.ModelChoiceField(label="Producto", queryset=Product.objects.all())
    code = forms.CharField(label="Lote verificado", max_length=100)
    expiry = forms.DateField(label="Caducidad verificada", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    location = forms.CharField(label="Ubicacion", max_length=120)
    packages = forms.IntegerField(label="Numero de cajas / envases", min_value=1, max_value=1000)
    content = forms.DecimalField(label="Contenido por caja / envase (unidad base)", min_value=Decimal("0.001"), max_digits=14, decimal_places=3)
    reason = forms.CharField(label="Motivo / referencia de recepcion", max_length=300, widget=forms.Textarea(attrs={"rows": 2}))
    verified = forms.BooleanField(label="Datos y saldo fisico verificados")
    request_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    def clean(self):
        values = super().clean()
        product, content = values.get("product"), values.get("content")
        if product and content:
            try:
                amount(content, product)
                if product.unit != "mL" and values.get("packages"):
                    amount(content * values["packages"], product)
            except forms.ValidationError as error:
                self.add_error("content", error)
        if product and product.requires_expiry and not values.get("expiry"):
            self.add_error("expiry", "Confirme la fecha del fabricante.")
        return values


class MovementForm(forms.Form):
    quantity = forms.DecimalField(label="Cantidad (unidad base)", min_value=Decimal("0.001"), max_digits=14, decimal_places=3)
    reason = forms.CharField(label="Destino / motivo", max_length=300)
    request_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)


class OpeningForm(forms.Form):
    opened_on = forms.DateField(label="Fecha de apertura", initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    request_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)


class BatchStatusForm(forms.Form):
    status = forms.ChoiceField(label="Estado del lote", choices=Batch.Status.choices)
    reason = forms.CharField(label="Motivo del cambio", max_length=300)


class ReverseForm(forms.Form):
    reason = forms.CharField(label="Motivo de la reversion", max_length=300)
    request_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)


class UploadForm(forms.Form):
    file = forms.FileField(label="Libro de inventario (.xlsx)", widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}))

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith(".xlsx") or uploaded.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Seleccione un XLSX de hasta 5 MB.")
        return uploaded


class MailForm(forms.Form):
    client_id = forms.UUIDField(label="ID publico de aplicacion Microsoft", required=False)
    recipients = forms.CharField(label="Destinatarios (uno por linea)", required=False, widget=forms.Textarea(attrs={"rows": 4}))
    enabled = forms.BooleanField(label="Habilitar notificaciones por correo", required=False)

    def clean_recipients(self):
        from django.core.validators import validate_email

        recipients = list(dict.fromkeys(value.strip() for value in self.cleaned_data["recipients"].splitlines() if value.strip()))
        if len(recipients) > 20:
            raise forms.ValidationError("Maximo 20 destinatarios.")
        for recipient in recipients:
            validate_email(recipient)
        return recipients

    def clean(self):
        values = super().clean()
        if values.get("enabled") and (not values.get("client_id") or not values.get("recipients")):
            raise forms.ValidationError("Para habilitar correo indique ID de aplicacion y destinatarios.")
        return values