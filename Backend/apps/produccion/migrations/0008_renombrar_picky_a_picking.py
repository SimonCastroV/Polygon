"""
La estación se llama Picking, no Picky.

- Las cuatro columnas de la liberación a Picking se RENOMBRAN (RenameField),
  no se borran y recrean: así las fechas, operarios y cuentas ya registrados
  se conservan tal cual.
- El valor del estado 'picky' pasa a 'picking' en las OP que estén ahí.
- El historial se corrige también (transiciones de estado y el campo del
  operario), para que la trazabilidad de las OP ya existentes use el mismo
  nombre que el resto del sistema.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def a_picking(apps, schema_editor):
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    Historial = apps.get_model('produccion', 'HistorialOrdenProduccion')
    OrdenProduccion.objects.filter(estado='picky').update(estado='picking')
    Historial.objects.filter(valor_anterior='picky').update(valor_anterior='picking')
    Historial.objects.filter(valor_nuevo='picky').update(valor_nuevo='picking')
    Historial.objects.filter(campo='nombre_operario_picky').update(
        campo='nombre_operario_picking'
    )


def a_picky(apps, schema_editor):
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    Historial = apps.get_model('produccion', 'HistorialOrdenProduccion')
    OrdenProduccion.objects.filter(estado='picking').update(estado='picky')
    Historial.objects.filter(valor_anterior='picking').update(valor_anterior='picky')
    Historial.objects.filter(valor_nuevo='picking').update(valor_nuevo='picky')
    Historial.objects.filter(campo='nombre_operario_picking').update(
        campo='nombre_operario_picky'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0007_ordenproduccion_grupo_critico_pesaje'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='ordenproduccion',
            old_name='fecha_envio_picky',
            new_name='fecha_envio_picking',
        ),
        migrations.RenameField(
            model_name='ordenproduccion',
            old_name='nombre_operario_picky',
            new_name='nombre_operario_picking',
        ),
        migrations.RenameField(
            model_name='ordenproduccion',
            old_name='recibida_por_picky',
            new_name='recibida_por_picking',
        ),
        migrations.RenameField(
            model_name='ordenproduccion',
            old_name='fecha_recepcion_picky',
            new_name='fecha_recepcion_picking',
        ),
        migrations.AlterField(
            model_name='ordenproduccion',
            name='recibida_por_picking',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ordenes_recibidas_picking',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='ordenproduccion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('produccion', 'En Producción'),
                    ('picking', 'En Picking'),
                    ('pesaje', 'En Pesaje'),
                    ('supervision_pesaje', 'En supervisión de Pesaje'),
                    ('mezcla', 'En Mezcla'),
                    ('extrusion', 'En Extrusión'),
                    ('calidad', 'En Calidad'),
                    ('empaque', 'En Empaque'),
                    ('finalizada', 'Finalizada'),
                    ('cancelada', 'Cancelada'),
                ],
                default='produccion',
                max_length=20,
            ),
        ),
        migrations.RunPython(a_picking, a_picky),
    ]
