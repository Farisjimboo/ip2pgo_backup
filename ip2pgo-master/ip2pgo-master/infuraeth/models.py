from django.db import models

# to be deprecated
class TradeStatus(models.Model):
    offer_id = models.CharField(max_length=6)
    released_eth = models.BooleanField(default=False)
    paid_penalty = models.BooleanField(default=False)
    made_payment = models.BooleanField(default=False)
    trade_prepped = models.BooleanField(default=False)
    paid_fees = models.BooleanField(default = False)
    buyer_comment = models.CharField(max_length=255, blank=True, null=True)
    seller_comment = models.CharField(max_length=255, blank=True, null=True)

class NonceManager(models.Model):
    nonce = models.IntegerField()
