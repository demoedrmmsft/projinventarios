from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from inventory import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", views.LocalLoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("setup/", views.setup, name="setup"),
    path("", views.dashboard, name="dashboard"),
    path("products/", views.products, name="products"),
    path("stocks/", views.stock_list, name="stock_list"),
    path("stocks/new/", views.receive_stock, name="receive"),
    path("stocks/<int:pk>/", views.stock_detail, name="stock_detail"),
    path("movements/", views.movements, name="movements"),
    path("movements/export/", views.export_movements, name="export_movements"),
    path("movements/<int:pk>/reverse/", views.reverse_movement, name="reverse"),
    path("imports/", views.imports, name="imports"),
    path("imports/<int:pk>/", views.import_detail, name="import_detail"),
    path("imports/rows/<int:source_id>/", views.receive_stock, name="confirm_row"),
    path("alerts/", views.alerts, name="alerts"),
    path("settings/mail/", views.mail_settings, name="mail_settings"),
]