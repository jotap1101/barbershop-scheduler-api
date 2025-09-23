from django.contrib import admin
from django.db.models import Avg
from django.utils.html import format_html

from apps.review.models import Review


class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface para o modelo Review com funcionalidades avançadas.
    """

    list_display = [
        "id_short",
        "customer_name",
        "barber_name",
        "service_name",
        "barbershop_name",
        "rating_stars",
        "has_comment_display",
        "review_type",
        "created_at",
        "is_recent",
    ]

    list_filter = ["rating", "created_at", "barbershop", "service", "barber"]

    search_fields = [
        "barbershop_customer__customer__first_name",
        "barbershop_customer__customer__last_name",
        "barbershop_customer__customer__username",
        "barber__first_name",
        "barber__last_name",
        "service__name",
        "barbershop__name",
        "comment",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "rating_stars_display",
        "customer_info",
        "barber_info",
        "service_info",
        "barbershop_info",
        "review_age_display",
    ]

    fieldsets = [
        (
            "Informações Básicas",
            {"fields": ("id", "rating", "rating_stars_display", "comment")},
        ),
        (
            "Relacionamentos",
            {
                "fields": (
                    "barbershop_customer",
                    "customer_info",
                    "barber",
                    "barber_info",
                    "service",
                    "service_info",
                    "barbershop",
                    "barbershop_info",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at", "review_age_display")}),
    ]

    list_per_page = 10
    list_max_show_all = 100

    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    actions_on_top = True
    actions_on_bottom = True
    list_select_related = [
        "barbershop_customer",
        "barbershop_customer__customer",
        "barber",
        "service",
        "barbershop",
    ]

    actions = ["mark_as_featured", "export_reviews", "calculate_statistics"]

    def get_queryset(self, request):
        """Otimiza consultas com select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "barbershop_customer",
                "barbershop_customer__customer",
                "barber",
                "service",
                "barbershop",
            )
        )

    def id_short(self, obj):
        """Exibe versão curta do ID"""
        return str(obj.id)[:8] + "..."

    id_short.short_description = "ID"

    def customer_name(self, obj):
        """Exibe o nome do cliente"""
        return obj.get_customer_name()

    customer_name.short_description = "Cliente"
    customer_name.admin_order_field = "barbershop_customer__customer__first_name"

    def barber_name(self, obj):
        """Exibe o nome do barbeiro"""
        return obj.get_barber_name()

    barber_name.short_description = "Barbeiro"
    barber_name.admin_order_field = "barber__first_name"

    def service_name(self, obj):
        """Exibe o nome do serviço"""
        return obj.get_service_name()

    service_name.short_description = "Serviço"
    service_name.admin_order_field = "service__name"

    def barbershop_name(self, obj):
        """Exibe o nome da barbearia"""
        return obj.get_barbershop_name()

    barbershop_name.short_description = "Barbearia"
    barbershop_name.admin_order_field = "barbershop__name"

    def rating_stars(self, obj):
        """Exibe as estrelas da avaliação"""
        return obj.get_rating_stars()

    rating_stars.short_description = "Avaliação"
    rating_stars.admin_order_field = "rating"

    def rating_stars_display(self, obj):
        """Exibe as estrelas da avaliação com cor"""
        stars = obj.get_rating_stars()
        if obj.rating >= 4:
            color = "green"
        elif obj.rating <= 2:
            color = "red"
        else:
            color = "orange"

        return format_html(
            '<span style="color: {}; font-size: 16px;">{}</span>', color, stars
        )

    rating_stars_display.short_description = "Avaliação Visual"

    def has_comment_display(self, obj):
        """Exibe se tem comentário"""
        if obj.has_comment():
            return format_html('<span style="color: green;">✓ Sim</span>')
        return format_html('<span style="color: red;">✗ Não</span>')

    has_comment_display.short_description = "Comentário"
    has_comment_display.admin_order_field = "comment"

    def review_type(self, obj):
        """Exibe o tipo da avaliação (positiva, negativa, neutra)"""
        if obj.is_positive_review():
            return format_html(
                '<span style="color: green; font-weight: bold;">Positiva</span>'
            )
        elif obj.is_negative_review():
            return format_html(
                '<span style="color: red; font-weight: bold;">Negativa</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Neutra</span>'
            )

    review_type.short_description = "Tipo"

    def is_recent(self, obj):
        """Indica se a avaliação é recente"""
        if obj.is_recent_review():
            return format_html('<span style="color: green;">✓ Recente</span>')
        return format_html('<span style="color: gray;">Antiga</span>')

    is_recent.short_description = "Recente"

    def customer_info(self, obj):
        """Informações detalhadas do cliente"""
        customer = obj.barbershop_customer.customer
        if customer:
            return format_html(
                "<strong>Nome:</strong> {}<br>"
                "<strong>Email:</strong> {}<br>"
                "<strong>Username:</strong> {}",
                customer.get_display_name(),
                customer.email,
                customer.username,
            )
        return "Cliente não encontrado"

    customer_info.short_description = "Info do Cliente"

    def barber_info(self, obj):
        """Informações detalhadas do barbeiro"""
        barber = obj.barber
        return format_html(
            "<strong>Nome:</strong> {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Username:</strong> {}",
            barber.get_display_name(),
            barber.email,
            barber.username,
        )

    barber_info.short_description = "Info do Barbeiro"

    def service_info(self, obj):
        """Informações detalhadas do serviço"""
        service = obj.service
        return format_html(
            "<strong>Nome:</strong> {}<br>"
            "<strong>Preço:</strong> {}<br>"
            "<strong>Duração:</strong> {}",
            service.name,
            service.get_formatted_price(),
            service.get_formatted_duration(),
        )

    service_info.short_description = "Info do Serviço"

    def barbershop_info(self, obj):
        """Informações detalhadas da barbearia"""
        barbershop = obj.barbershop
        return format_html(
            "<strong>Nome:</strong> {}<br>"
            "<strong>Endereço:</strong> {}<br>"
            "<strong>Proprietário:</strong> {}",
            barbershop.name,
            barbershop.address,
            barbershop.owner.get_display_name(),
        )

    barbershop_info.short_description = "Info da Barbearia"

    def review_age_display(self, obj):
        """Exibe a idade da avaliação"""
        days = obj.get_review_age_days()
        if days == 0:
            return "Hoje"
        elif days == 1:
            return "1 dia atrás"
        else:
            return f"{days} dias atrás"

    review_age_display.short_description = "Idade da Avaliação"

    def mark_as_featured(self, request, queryset):
        """Ação customizada para marcar como destaque"""
        # Esta seria uma funcionalidade futura
        self.message_user(
            request, f"{queryset.count()} avaliações marcadas como destaque."
        )

    mark_as_featured.short_description = "Marcar como destaque"

    def export_reviews(self, request, queryset):
        """Ação para exportar avaliações"""
        # Implementação de export seria adicionada aqui
        self.message_user(request, f"{queryset.count()} avaliações exportadas.")

    export_reviews.short_description = "Exportar avaliações selecionadas"

    def calculate_statistics(self, request, queryset):
        """Calcula estatísticas das avaliações selecionadas"""
        total = queryset.count()
        avg_rating = queryset.aggregate(avg=Avg("rating"))["avg"] or 0
        positive = queryset.filter(rating__gte=4).count()
        negative = queryset.filter(rating__lte=2).count()

        self.message_user(
            request,
            f"Estatísticas: {total} avaliações, "
            f"média {avg_rating:.2f}, "
            f"{positive} positivas, "
            f"{negative} negativas.",
        )

    calculate_statistics.short_description = "Calcular estatísticas"


# Registrar o modelo no admin
admin.site.register(Review, ReviewAdmin)
