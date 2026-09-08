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
        'ordenes/<int:pk>/enviar-picky/',
        views.OrdenProduccionEnviarPickyView.as_view(),
        name='ordenes-enviar-picky',
    ),
    path(
        'ordenes/<int:pk>/recepcion-picky/',
        views.OrdenProduccionRecepcionPickyView.as_view(),
        name='ordenes-recepcion-picky',
    ),
    path(
        'ordenes/<int:pk>/enviar-pesaje/',
        views.OrdenProduccionEnviarPesajeView.as_view(),
        name='ordenes-enviar-pesaje',
    ),
]
