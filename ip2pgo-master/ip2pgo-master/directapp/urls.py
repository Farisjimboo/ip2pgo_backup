from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login_security', views.login_security, name='login_security'),
    path('web', views.web, name='web'),
    path('security/<username>', views.security, name='security'),
    path('update_profile/<token>/<security_code>/<crypto>', views.update_profile, name='update_profile'),
    path('home/<token>/<security_code>/<crypto>', views.home, name='home'),
    path('menu/<token>/<security_code>/<crypto>', views.menu, name='menu'),
    path('mainpage/<token>/<security_code>/<crypto>', views.mainpage, name='mainpage'),
    path('profile/<token>/<security_code>/<crypto>', views.profile, name='profile'),
    path('create_wallet/<token>/<security_code>/<crypto>', views.create_wallet, name='create_wallet'),
    path('deposit/<token>/<security_code>/<crypto>', views.deposit, name='deposit'),
    path('withdrawal/<token>/<security_code>/<crypto>', views.withdrawal, name='withdrawal'),
    path('passcode/<token>/<security_code>/<offer_id>/<amount>/<fiat>/<crypto>', views.passcode, name='passcode'),
    path('buy_list/<token>/<security_code>/<crypto>', views.buy_list, name='buy_list'),
    path('sell_list/<token>/<security_code>/<crypto>', views.sell_list, name='sell_list'),
    path('order_list/<token>/<security_code>/<crypto>', views.order_list, name='order_list'),
    path('buying/<token>/<security_code>/<offer_id>/<crypto>', views.buying, name='buying'),
    path('selling/<token>/<security_code>/<offer_id>/<crypto>', views.selling, name='selling'),
    path('editing/<token>/<security_code>/<listing>/<offer_id>/<crypto>', views.editing, name='editing'),
    path('prep_trade/<token><security_code>/<offer_id>/<amount>/<fiat>/<crypto>', views.prep_trade, name='prep_trade'),
    path('payment_confirm/<token>/<security_code>/<offer_id>/<crypto>', views.payment_confirm, name='payment_confirm'),
    path('otc_confirm/<token>/<security_code>/<offer_id>/<crypto>', views.otc_confirm, name='otc_confirm'),
    path('chat/<token>/<security_code>/<offer_id>/<crypto>', views.chat, name='chat'),
    path('chat_message/<token>/<security_code>/<offer_id>/<crypto>', views.chat_message, name='chat_message'),
    path('dispute/<token>/<security_code>/<offer_id>/<crypto>', views.dispute, name='dispute'),
    path('create_buy_offer/<token>/<security_code>/<crypto>', views.create_buy_offer, name='create_buy_offer'),
    path('create_sell_offer/<token>/<security_code>/<crypto>', views.create_sell_offer, name='create_sell_offer'),
    path('wallet/<token>/<security_code>/<crypto>', views.wallet, name='wallet'),
    path('sync/<token>/<security_code>/<crypto>', views.sync, name='sync'),
    path('support/<token>/<security_code>/<crypto>', views.support, name='support'),
    path('order_list/<token>/<security_code>/<crypto>', views.order_list, name='order_list'),
    path('history/<token>/<security_code>/<crypto>', views.history, name='history'),
    path('complete/<token>/<security_code>/<activity>/<address>/<offer_id>/<crypto>', views.complete, name='complete'),
    path('logout/<security_code>/<crypto>', views.logout, name='logout'),
    path('thankyou/<token>/<security_code>/<crypto>', views.thankyou, name='thankyou')
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


