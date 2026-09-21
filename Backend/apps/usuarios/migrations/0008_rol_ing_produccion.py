"""
Nuevo rol Ing. Producción: acompaña las OP de hoja azul (acompañamiento de
IP) y consulta su proceso completo, sin editarlo. Solo cambian las opciones
del campo; ninguna cuenta existente cambia de rol.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_renombrar_rol_picky_a_picking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrador'),
                    ('supervisor', 'Supervisor'),
                    ('produccion', 'Producción'),
                    ('ing_produccion', 'Ing. Producción'),
                    ('picking', 'Picking'),
                    ('pesaje', 'Pesaje'),
                    ('mezcla', 'Mezcla'),
                    ('extrusion', 'Extrusión'),
                    ('calidad', 'Calidad'),
                    ('empaque', 'Empaque'),
                    ('planta', 'Personal de Planta'),
                ],
                default='planta',
                max_length=20,
            ),
        ),
    ]
