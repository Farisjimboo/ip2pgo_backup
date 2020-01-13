from django.urls import path
from django.conf import settings
from django.conf.urls import url, include
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('<country>', views.login, name='login'),
    path('list/<country>/<admin_name>', views.list, name='list'),
    path('dispute/<country>/<admin_name>', views.dispute, name='dispute'),
    path('adminchat/<country>/<admin_name>/<offer_id>', views.chat, name='chat_admin'),
    path('verify/<country>/<admin_name>/<offer_id>/<user>', views.verify, name='verify'),
    path('list_allusers/<country>/<admin_name>', views.list_allusers, name='list_allusers'),
    path('list_newusers/<country>/<admin_name>', views.list_newusers, name='list_newusers'),
    path('list_unverifiedusers/<country>/<admin_name>', views.list_unverifiedusers, name='list_unverifiedusers'),
    path('histories/<country>/<admin_name>/<username>', views.histories, name='histories'),
    path('support_chat/<country>/<admin_name>/<offer_id>', views.support_chat, name='support_chat'),
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
