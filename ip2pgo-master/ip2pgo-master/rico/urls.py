from django.urls import path
from django.conf import settings
from django.conf.urls import url, include
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('login', views.login, name='ricologin'),
    path('main/<security_code>', views.main, name='ricomain'),
    path('register', views.register, name='ricoregister'),
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
