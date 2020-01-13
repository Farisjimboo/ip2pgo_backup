from django.urls import path
from django.conf import settings
from django.conf.urls.static import static  
from django.conf.urls.static import static 
from django.conf.urls import url, include 
from . import views

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
    path('referralwebsite/', views.referralwebsite, name='referralwebsite'),
    path('error/', views.error, name='error'),
    path('rewards/', views.rewards, name='rewards'),
    path('contact/', views.contact, name='contact'),
    path('rewards/', views.rewards, name='rewards'),
    path('rico_termsheet/', views.rico_termsheet, name='rico_termsheet'),
    path('registration/<country>', views.registration, name='registration'),
    path('registration/<country>/<referral_id>', views.registration_refer, name='registration_refer'),
    path('register_country/', views.register_country, name='register_country'),
    path('country/', views.country, name='country'),
    path('userguide/', views.userguide, name='userguide'),
    path('', views.website, name='website'),
    path('terms/', views.terms, name='terms'),
    path('faq/', views.faq, name='faq'),
    path('termsofuse/', views.termsofuse, name='termsofuse'),
    path('policy/', views.policy, name='policy'),
    path('loading/<country>', views.loading, name='loading'),
    path('download/<country>', views.download, name='download'),
    path('ip2pgoterms', views.ip2pgoterms, name='ip2pgoterms'),
    path('otc_userguide', views.otc_userguide, name='otc_userguide'),
    path('fiat_userguide', views.fiat_userguide, name='fiat_userguide'),
    path('dividends', views.dividends, name='dividends'),
    path('categories', views.categories, name='categories'),
    path('login_categories', views.login_categories, name='login_categories'),
    path('register_otc', views.register_otc, name='register_otc'),
    path('login_otc', views.login_otc, name='login_otc'),
    path('main', views.rico_main, name='rico_main'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)                                                                                                                                                                                         
