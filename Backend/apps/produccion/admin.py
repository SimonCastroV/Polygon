from django.contrib import admin

from .models import HistorialOrdenProduccion, OrdenProduccion


@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    list_display = (
        'numero_orden',
        'producto',
        'cantidad',
        'urgente',
        'estado',
        'creado_por',
        'fecha_creacion',
    )
    list_filter = ('estado', 'urgente')
    search_fields = ('numero_orden', 'producto', 'materia_prima')
    readonly_fields = ('numero_orden', 'fecha_creacion', 'fecha_modificacion')


@admin.register(HistorialOrdenProduccion)
class HistorialOrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ('orden', 'campo', 'valor_anterior', 'valor_nuevo', 'modificado_por', 'fecha')
    list_filter = ('campo',)
    readonly_fields = ('orden', 'modificado_por', 'campo', 'valor_anterior', 'valor_nuevo', 'fecha')
