"""
El operario de Pesaje ya no digita el peso real de cada materia prima: solo
ve la cantidad de la fórmula que debe pesar. La tabla de pesos reales queda
sin uso y se elimina.

Al revertir, la tabla se vuelve a crear vacía (los pesos que tuviera no se
recuperan desde la migración).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pesaje', '0003_registropesaje_fecha_inicio_pesaje'),
    ]

    operations = [
        migrations.DeleteModel(name='PesoMaterial'),
    ]
