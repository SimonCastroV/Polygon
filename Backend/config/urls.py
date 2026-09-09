from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.pesaje.urls import catalogo_urlpatterns as pesaje_catalogo


def health(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/', include('apps.usuarios.urls')),
    path('api/produccion/', include('apps.produccion.urls')),
    path('api/pesaje/', include((pesaje_catalogo, 'pesaje'))),
]
