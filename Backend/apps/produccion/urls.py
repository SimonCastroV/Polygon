from django.urls import include, path

from . import views

urlpatterns = [
    path('ordenes/<int:pk>/pesaje/', include('apps.pesaje.urls')),
    path(
        'ordenes/',
        views.OrdenProduccionListView.as_view(),
        name='ordenes-list',
    ),
    path(
        'ordenes/<int:pk>/',
        views.OrdenProduccionDetailView.as_view(),
        name='ordenes-detail',
    ),
    path(
        'ordenes/<int:pk>/ingresar/',
        views.OrdenProduccionIngresarView.as_view(),
        name='ordenes-ingresar',
    ),
    path(
        'ordenes/<int:pk>/enviar-picking/',
        views.OrdenProduccionEnviarPickingView.as_view(),
        name='ordenes-enviar-picking',
    ),
    path(
        'ordenes/<int:pk>/recepcion-picking/',
        views.OrdenProduccionRecepcionPickingView.as_view(),
        name='ordenes-recepcion-picking',
    ),
    path(
        'ordenes/<int:pk>/enviar-pesaje/',
        views.OrdenProduccionEnviarPesajeView.as_view(),
        name='ordenes-enviar-pesaje',
    ),
]
