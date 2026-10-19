from django.contrib import admin

from .models import AuditEvent, Batch, ImportFile, ImportRow, MailConfiguration, Movement, Notification, Product, Stock


class ReadOnlyAdmin(admin.ModelAdmin):
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in [Product, Batch, Stock, Movement, ImportFile, ImportRow, AuditEvent, Notification, MailConfiguration]:
    admin.site.register(model, ReadOnlyAdmin)

admin.site.site_header = "Lote LAB - Administracion"
admin.site.site_title = "Lote LAB"
admin.site.index_title = "Usuarios y consulta de registros"