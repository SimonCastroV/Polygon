from django.urls import path

from . import views

urlpatterns = [
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
]
