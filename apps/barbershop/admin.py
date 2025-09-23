from django.contrib import admin
from django.utils.html import format_html

from .models import Barbershop, Service, BarbershopCustomer


@admin.register(Barbershop)
class BarbershopAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "owner",
        "address",
        "phone",
        "email",
        "get_services_count",
        "get_customers_count",
        "created_at",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "name",
        "cnpj",
        "address",
        "email",
        "owner__first_name",
        "owner__last_name",
        "owner__username",
    ]
    ordering = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 10
    list_max_show_all = 100
    actions_on_top = True
    actions_on_bottom = True

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "id",
                    "name",
                    "description",
                    "logo",
                )
            },
        ),
        (
            "Dados Comerciais",
            {
                "fields": (
                    "cnpj",
                    "owner",
                )
            },
        ),
        (
            "Contato",
            {
                "fields": (
                    "address",
                    "phone",
                    "email",
                    "website",
                )
            },
        ),
        (
            "Metadados",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_services_count(self, obj):
        return obj.services.count()

    get_services_count.short_description = "Serviços"

    def get_customers_count(self, obj):
        return obj.barbershopcustomer_set.count()

    get_customers_count.short_description = "Clientes"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "barbershop",
        "price_formatted",
        "get_duration_minutes",
        "available",
        "created_at",
    ]
    list_filter = [
        "available",
        "barbershop",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "name",
        "description",
        "barbershop__name",
    ]
    ordering = ["barbershop__name", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["available"]
    actions_on_top = True
    actions_on_bottom = True

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "id",
                    "name",
                    "description",
                    "barbershop",
                )
            },
        ),
        (
            "Preço e Duração",
            {
                "fields": (
                    "price",
                    "duration",
                    "available",
                )
            },
        ),
        ("Imagem", {"fields": ("image",)}),
        (
            "Metadados",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def price_formatted(self, obj):
        return f"R$ {obj.price:.2f}"

    price_formatted.short_description = "Preço"

    def get_duration_minutes(self, obj):
        return obj.get_duration_in_minutes()

    get_duration_minutes.short_description = "Duração (min)"

    actions = ["mark_as_active", "mark_as_inactive"]

    def mark_as_active(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f"{updated} serviço(s) marcado(s) como ativo(s).")

    mark_as_active.short_description = "Marcar como ativo"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f"{updated} serviço(s) marcado(s) como inativo(s).")

    mark_as_inactive.short_description = "Marcar como inativo"


@admin.register(BarbershopCustomer)
class BarbershopCustomerAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "barbershop",
        "get_customer_name",
        "get_customer_email",
        "last_visit",
        "get_appointments_count",
    ]
    list_filter = [
        "barbershop",
        "last_visit",
    ]
    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__email",
        "customer__username",
        "barbershop__name",
    ]
    ordering = ["-last_visit"]
    readonly_fields = ["id"]
    list_per_page = 10
    list_max_show_all = 100
    actions_on_top = True
    actions_on_bottom = True

    def get_customer_name(self, obj):
        if obj.customer:
            return (
                f"{obj.customer.first_name} {obj.customer.last_name}".strip()
                or obj.customer.username
            )
        return "Cliente removido"

    get_customer_name.short_description = "Nome Completo"

    def get_customer_email(self, obj):
        if obj.customer:
            return obj.customer.email
        return "---"

    get_customer_email.short_description = "Email"

    def get_appointments_count(self, obj):
        return obj.get_total_appointments()

    get_appointments_count.short_description = "Agendamentos"
