"""ip2pdirect URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from directapp import urls as urlsapp
from ip2pwebsite import urls as urlsweb
from dispute import urls as urlsdispute
from ip2padmin import urls as urlsip2padmin
from rico import urls as urlsrico
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import handler404, handler500
from directapp import views as directapp_views
#from infuraeth import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dispute/', include(urlsdispute)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 

   
urlpatterns += i18n_patterns(
    path('',include(urlsweb)),
    path('app/<country>/', include(urlsapp)),
    path('ip2padmin/', include(urlsip2padmin)),
    path('rico/', include(urlsrico)),
)

handler404 = directapp_views.handler404
handler500 = directapp_views.handler500
