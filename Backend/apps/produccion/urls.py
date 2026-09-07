from django.urls import path

from . import views

urlpatterns = [
    path(
        'ordenes/',
        views.OrdenProduccionListCreateView.as_view(),
        name='ordenes-list-create',
    ),
    path(
        'ordenes/<int:pk>/',
        views.OrdenProduccionDetailUpdateView.as_view(),
        name='ordenes-detail-update',
    ),
]
