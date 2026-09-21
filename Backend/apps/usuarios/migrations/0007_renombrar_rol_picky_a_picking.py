"""
La estación se llama Picking, no Picky. Renombra el valor del rol y convierte
las cuentas que ya lo tenían, para que no queden con un rol huérfano y sin
permisos. El nombre de usuario de cada cuenta no se toca: es un dato de cada
instalación, no del esquema.
"""

from django.db import migrations, models


def a_picking(apps, schema_editor):
    CustomUser = apps.get_model('usuarios', 'CustomUser')
    CustomUser.objects.filter(rol='picky').update(rol='picking')


def a_picky(apps, schema_editor):
    CustomUser = apps.get_model('usuarios', 'CustomUser')
    CustomUser.objects.filter(rol='picking').update(rol='picky')


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_quitar_rol_supervisor_pesaje'),
    ]

    operations = [
        migrations.RunPython(a_picking, a_picky),
        migrations.AlterField(
            model_name='customuser',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrador'),
                    ('supervisor', 'Supervisor'),
                    ('produccion', 'Producción'),
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
