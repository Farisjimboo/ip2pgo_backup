from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('buyer-proof/<offer_id>', views.buyer_proof, name='buyer_proof'),
    path('seller-proof/<offer_id>', views.seller_proof, name='seller_proof'), 
    path('conclude-buyer/<offer_id>', views.conclude_buyer, name='buyer_win'),
    path('conclude-seller/<offer_id>', views.conclude_seller, name='seller_win'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
