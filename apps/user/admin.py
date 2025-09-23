from apps.user.models import User
from django.contrib import admin
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "get_full_name_display",
        "is_staff",
        "is_active",
        "date_joined",
        "last_login",
        "get_user_type",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "date_joined",
        "last_login",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")
    list_per_page = 10
    list_max_show_all = 100
    list_editable = ("is_active",)
    actions_on_top = True
    actions_on_bottom = True
    date_hierarchy = "date_joined"

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "id",
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Datas Importantes",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_full_name_display(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else "---"

    get_full_name_display.short_description = "Nome Completo"

    def get_user_type(self, obj):
        if obj.is_superuser:
            return format_html(
                '<span style="color: red; font-weight: bold;">Super Admin</span>'
            )
        elif obj.is_staff:
            return format_html(
                '<span style="color: blue; font-weight: bold;">Staff</span>'
            )
        else:
            return format_html('<span style="color: green;">Usuário</span>')

    get_user_type.short_description = "Tipo"

    actions = ["activate_users", "deactivate_users"]

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuário(s) ativado(s).")

    activate_users.short_description = "Ativar usuários selecionados"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} usuário(s) desativado(s).")

    deactivate_users.short_description = "Desativar usuários selecionados"
