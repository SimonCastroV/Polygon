"""
La clase de OP sigue el color de la hoja física: blanca (proceso normal),
amarilla (urgente) y azul (requiere acompañamiento de IP). La tercera opción
se había nombrado "Producto peligroso"; pasa a ser "Acompañamiento de IP".

"Producto peligroso" es una característica del producto, no de la hoja: se
mueve al grupo de producto para Pesaje y ocupa el lugar de "Hojas azules",
que dejó de tener sentido ahí porque la hoja azul es la clase de la OP. Sigue
siendo un grupo crítico, así que las OP que ya respondieron el formulario de
condiciones críticas conservan un grupo coherente con él.

Los valores se convierten también en el historial, igual que en 0008, para
que la trazabilidad use los mismos valores que el resto del sistema. El
texto legible del historial (detalle) conserva lo que se mostró en su
momento.
"""

from django.db import migrations, models

CONVERSIONES = [
    # (campo, valor anterior, valor nuevo)
    ('clasificacion', 'peligroso', 'acompanamiento_ip'),
    ('grupo_critico_pesaje', 'hojas_azules', 'producto_peligroso'),
]


def convertir(apps, sentido):
    OrdenProduccion = apps.get_model('produccion', 'OrdenProduccion')
    Historial = apps.get_model('produccion', 'HistorialOrdenProduccion')
    for campo, anterior, nuevo in CONVERSIONES:
        desde, hacia = (anterior, nuevo) if sentido == 'adelante' else (nuevo, anterior)
        OrdenProduccion.objects.filter(**{campo: desde}).update(**{campo: hacia})
        eventos = Historial.objects.filter(campo=campo)
        eventos.filter(valor_anterior=desde).update(valor_anterior=hacia)
        eventos.filter(valor_nuevo=desde).update(valor_nuevo=hacia)


def adelante(apps, schema_editor):
    convertir(apps, 'adelante')


def atras(apps, schema_editor):
    convertir(apps, 'atras')


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0008_renombrar_picky_a_picking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordenproduccion',
            name='clasificacion',
            field=models.CharField(
                choices=[
                    ('urgente', 'Urgente'),
                    ('acompanamiento_ip', 'Acompañamiento de IP'),
                    ('normal', 'Proceso normal'),
                ],
                default='normal',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='ordenproduccion',
            name='grupo_critico_pesaje',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Sin clasificar'),
                    ('no_critico', 'No crítico'),
                    ('blancos', 'Blancos'),
                    ('aditivos_retardantes', 'Aditivos / Retardantes a la Llama'),
                    ('producto_peligroso', 'Producto peligroso'),
                ],
                default='',
                help_text='Clasificar según el código de producto y su ficha técnica. '
                'Obligatorio antes de enviar Pesaje a supervisión.',
                max_length=20,
            ),
        ),
        migrations.RunPython(adelante, atras),
    ]
