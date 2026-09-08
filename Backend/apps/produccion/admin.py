from django.contrib import admin

from .models import HistorialOrdenProduccion, MaterialOrden, OrdenProduccion


class MaterialOrdenInline(admin.TabularInline):
    model = MaterialOrden
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    """
    Mientras no exista la integración con la base de datos de Sumicolor,
    esta es la pantalla donde se carga el encabezado + los materiales de
    cada OP (ver docstring de OrdenProduccion). La API REST de Polygon solo
    expone estos datos en modo lectura.
    """

    inlines = [MaterialOrdenInline]
    list_display = (
        'numero_orden',
        'codigo_producto',
        'referencia',
        'cliente',
        'cantidad',
        'clasificacion',
        'grupo_critico_pesaje',
        'estado',
        'creado_por',
        'fecha_creacion',
    )
    list_filter = ('estado', 'clasificacion', 'grupo_critico_pesaje')
    search_fields = ('numero_orden', 'codigo_producto', 'referencia', 'cliente', 'pedido')
    readonly_fields = ('numero_orden', 'fecha_creacion', 'fecha_modificacion')

    def get_readonly_fields(self, request, obj=None):
        # La clasificación revisada no puede cambiar ni ocultar respuestas tras un envío.
        if (
            obj
            and obj.grupo_critico_pesaje
            and hasattr(obj, 'pesaje')
            and obj.pesaje.fecha_envio_supervision
        ):
            return (*self.readonly_fields, 'grupo_critico_pesaje')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        grupo_anterior = (
            OrdenProduccion.objects.get(pk=obj.pk).grupo_critico_pesaje if change else ''
        )
        if not obj.creado_por_id:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
        if grupo_anterior != obj.grupo_critico_pesaje:
            HistorialOrdenProduccion.objects.create(
                orden=obj,
                modificado_por=request.user,
                campo='grupo_critico_pesaje',
                valor_anterior=grupo_anterior,
                valor_nuevo=obj.grupo_critico_pesaje,
                detalle=f'Clasificación del producto {obj.codigo_producto}: '
                f'{obj.get_grupo_critico_pesaje_display()}',
            )


@admin.register(HistorialOrdenProduccion)
class HistorialOrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ('orden', 'campo', 'valor_anterior', 'valor_nuevo', 'modificado_por', 'fecha')
    list_filter = ('campo',)
    readonly_fields = (
        'orden',
        'modificado_por',
        'campo',
        'valor_anterior',
        'valor_nuevo',
        'fecha',
        'detalle',
    )
