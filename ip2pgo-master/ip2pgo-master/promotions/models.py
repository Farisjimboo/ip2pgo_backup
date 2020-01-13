from django.db import models

class Comissions(models.Model):
    date_gained = models.DateTimeField(auto_now_add=True)
    referer = models.CharField(max_length=255)
    trader = models.CharField(max_length=255)
    amount = models.DecimalField(decimal_places=0, max_digits=30, default=0)
    token = models.CharField(max_length=20, default="ETH")

class Redemption(models.Model):
    date_redeemed = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(decimal_places=0, max_digits=30, default=0)
    user = models.CharField(max_length=255)
    token = models.CharField(max_length=20, default="ETH")
