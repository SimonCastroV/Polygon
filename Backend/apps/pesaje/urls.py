from django.urls import path

from . import views

# Rutas por OP: se montan bajo produccion/ordenes/<pk>/pesaje/.
urlpatterns = [
    path('', views.GuardarPesajeView.as_view(), name='pesaje-guardar'),
    path('iniciar/', views.IniciarPesajeView.as_view(), name='pesaje-iniciar'),
    path('enviar-supervisor/', views.EnviarSupervisorView.as_view(), name='pesaje-enviar'),
    path('aprobar/', views.RevisarPesajeView.as_view(), name='pesaje-aprobar'),
    path('devolver/', views.DevolverPesajeView.as_view(), name='pesaje-devolver'),
]

# Rutas del módulo, sin OP asociada: se montan bajo api/pesaje/.
catalogo_urlpatterns = [
    path(
        'verificaciones/',
        views.VerificacionesPesajeView.as_view(),
        name='pesaje-verificaciones',
    ),
]
