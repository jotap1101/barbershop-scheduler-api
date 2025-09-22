from django.contrib import admin
from django.utils.html import format_html

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_customer_name",
        "get_service_name",
        "get_barbershop_name",
        "formatted_amount",
        "get_method_display_colored",
        "get_status_display_colored",
        "payment_date",
        "created_at",
    ]
    list_filter = [
        "status",
        "method",
        "payment_date",
        "created_at",
        "appointment__barbershop",
        "appointment__service",
    ]
    search_fields = [
        "appointment__customer__first_name",
        "appointment__customer__last_name",
        "appointment__service__name",
        "appointment__barbershop__name",
        "transaction_id",
        "notes",
    ]
    ordering = ["-created_at"]
    readonly_fields = [
        "id",
        "transaction_id",
        "created_at",
        "updated_at",
        "get_customer_name",
        "get_service_name",
        "get_barbershop_name",
        "get_formatted_amount",
        "get_payment_age_days",
    ]
    
    fieldsets = (
        ("Informações Básicas", {
            "fields": (
                "id",
                "appointment",
                "amount",
                "get_formatted_amount",
                "status",
                "method",
            )
        }),
        ("Detalhes do Pagamento", {
            "fields": (
                "transaction_id",
                "payment_date",
                "notes",
            )
        }),
        ("Informações do Agendamento", {
            "fields": (
                "get_customer_name",
                "get_service_name",
                "get_barbershop_name",
            ),
            "classes": ("collapse",)
        }),
        ("Metadados", {
            "fields": (
                "created_at",
                "updated_at",
                "get_payment_age_days",
            ),
            "classes": ("collapse",)
        }),
    )
    
    def get_customer_name(self, obj):
        return obj.get_customer_name()
    get_customer_name.short_description = "Cliente"
    
    def get_service_name(self, obj):
        return obj.get_service_name()
    get_service_name.short_description = "Serviço"
    
    def get_barbershop_name(self, obj):
        return obj.get_barbershop_name()
    get_barbershop_name.short_description = "Barbearia"
    
    def formatted_amount(self, obj):
        return obj.get_formatted_amount()
    formatted_amount.short_description = "Valor"
    
    def get_formatted_amount(self, obj):
        return obj.get_formatted_amount()
    get_formatted_amount.short_description = "Valor Formatado"
    
    def get_payment_age_days(self, obj):
        age = obj.get_payment_age_days()
        if age is None:
            return "Não pago"
        return f"{age} dias"
    get_payment_age_days.short_description = "Idade do Pagamento"
    
    def get_method_display_colored(self, obj):
        colors = {
            Payment.Method.PIX: "#00D4AA",
            Payment.Method.CREDIT_CARD: "#4CAF50",
            Payment.Method.DEBIT_CARD: "#2196F3",
            Payment.Method.CASH: "#FF9800",
        }
        color = colors.get(obj.method, "#757575")
        icon = obj.get_method_display_icon()
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_method_display()
        )
    get_method_display_colored.short_description = "Método"
    
    def get_status_display_colored(self, obj):
        colors = {
            Payment.Status.PENDING: "#FF9800",
            Payment.Status.PAID: "#4CAF50",
            Payment.Status.REFUNDED: "#F44336",
        }
        color = colors.get(obj.status, "#757575")
        icon = obj.get_status_display_icon()
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    get_status_display_colored.short_description = "Status"
    
    actions = ["mark_as_paid", "mark_as_refunded"]
    
    def mark_as_paid(self, request, queryset):
        """Ação para marcar pagamentos como pagos"""
        updated = 0
        for payment in queryset:
            if payment.status == Payment.Status.PENDING:
                payment.mark_as_paid()
                updated += 1
        
        self.message_user(
            request,
            f"{updated} pagamento(s) marcado(s) como pago(s)."
        )
    mark_as_paid.short_description = "Marcar como pago"
    
    def mark_as_refunded(self, request, queryset):
        """Ação para marcar pagamentos como reembolsados"""
        updated = 0
        for payment in queryset:
            if payment.status == Payment.Status.PAID:
                payment.mark_as_refunded()
                updated += 1
        
        self.message_user(
            request,
            f"{updated} pagamento(s) marcado(s) como reembolsado(s)."
        )
    mark_as_refunded.short_description = "Marcar como reembolsado"
    
    def has_delete_permission(self, request, obj=None):
        """Previne exclusão de pagamentos pagos ou reembolsados"""
        if obj and obj.status in [Payment.Status.PAID, Payment.Status.REFUNDED]:
            return False
        return super().has_delete_permission(request, obj)
