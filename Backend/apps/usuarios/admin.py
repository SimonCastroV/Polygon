from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, RegistroAuditoriaUsuario


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'first_name', 'last_name', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (('Polygon', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Polygon', {'fields': ('rol',)}),)


@admin.register(RegistroAuditoriaUsuario)
class RegistroAuditoriaUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'campo',
        'valor_anterior',
        'valor_nuevo',
        'modificado_por',
        'fecha',
    )
    list_filter = ('campo',)
    readonly_fields = (
        'usuario',
        'modificado_por',
        'campo',
        'valor_anterior',
        'valor_nuevo',
        'fecha',
    )
