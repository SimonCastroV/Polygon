from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('usuarios/', views.UsuarioListCreateView.as_view(), name='usuarios-list-create'),
    path(
        'usuarios/<int:pk>/cambiar-password/',
        views.CambiarPasswordView.as_view(),
        name='usuarios-cambiar-password',
    ),
]
