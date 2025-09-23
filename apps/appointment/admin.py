from django.contrib import admin

from .models import Appointment, BarberSchedule


@admin.register(BarberSchedule)
class BarberScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "barber",
        "barbershop",
        "get_weekday_display",
        "start_time",
        "end_time",
        "is_available",
        "get_work_duration_hours",
    ]
    list_filter = ["weekday", "is_available", "barbershop"]
    search_fields = [
        "barber__first_name",
        "barber__last_name",
        "barbershop__name",
    ]
    ordering = ["weekday", "start_time"]
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["is_available"]
    actions_on_top = True
    actions_on_bottom = True

    def get_work_duration_hours(self, obj):
        return f"{obj.get_work_duration_hours():.1f}h"

    get_work_duration_hours.short_description = "Duração (horas)"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "barber",
        "service",
        "barbershop",
        "start_datetime",
        "status",
        "final_price",
        "is_today",
    ]
    list_filter = [
        "status",
        "barbershop",
        "start_datetime",
        "created_at",
    ]
    search_fields = [
        "customer__customer__first_name",
        "customer__customer__last_name",
        "barber__first_name",
        "barber__last_name",
        "service__name",
        "barbershop__name",
    ]
    ordering = ["-start_datetime"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "start_datetime"
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ["status"]
    actions_on_top = True
    actions_on_bottom = True

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "customer",
                    "barber",
                    "service",
                    "barbershop",
                )
            },
        ),
        (
            "Horário",
            {
                "fields": (
                    "start_datetime",
                    "end_datetime",
                )
            },
        ),
        (
            "Status e Preço",
            {
                "fields": (
                    "status",
                    "final_price",
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

    def is_today(self, obj):
        return obj.is_today()

    is_today.boolean = True
    is_today.short_description = "Hoje"

    actions = ["mark_as_confirmed", "mark_as_completed", "mark_as_cancelled"]

    def mark_as_confirmed(self, request, queryset):
        updated = 0
        for appointment in queryset:
            if appointment.confirm():
                updated += 1
        self.message_user(request, f"{updated} agendamentos foram confirmados.")

    mark_as_confirmed.short_description = "Confirmar agendamentos selecionados"

    def mark_as_completed(self, request, queryset):
        updated = 0
        for appointment in queryset:
            if appointment.complete():
                updated += 1
        self.message_user(
            request, f"{updated} agendamentos foram marcados como concluídos."
        )

    mark_as_completed.short_description = "Marcar como concluídos"

    def mark_as_cancelled(self, request, queryset):
        updated = 0
        for appointment in queryset:
            if appointment.cancel():
                updated += 1
        self.message_user(request, f"{updated} agendamentos foram cancelados.")

    mark_as_cancelled.short_description = "Cancelar agendamentos selecionados"
