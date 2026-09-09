from django.urls import path

from . import views

urlpatterns = [
    path('', views.GuardarPesajeView.as_view(), name='pesaje-guardar'),
    path('iniciar/', views.IniciarPesajeView.as_view(), name='pesaje-iniciar'),
    path('enviar-supervisor/', views.EnviarSupervisorView.as_view(), name='pesaje-enviar'),
    path('aprobar/', views.RevisarPesajeView.as_view(), name='pesaje-aprobar'),
    path('devolver/', views.DevolverPesajeView.as_view(), name='pesaje-devolver'),
]
