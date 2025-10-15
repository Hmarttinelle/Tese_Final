# projeto_estrutural/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('calculos.urls')),
]

# Esta linha só funciona em modo de DEBUG e serve para que o servidor de 
# desenvolvimento do Django consiga encontrar e mostrar os ficheiros que carregar.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)