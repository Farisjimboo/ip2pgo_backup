from django.db import models

class UserProfile(models.Model):
    email = models.EmailField(primary_key=True)
    member_id = models.CharField(max_length=6)
    security_code = models.CharField(blank=True, null=True, max_length=15)
    referral_id = models.CharField(null=True, blank=True, max_length=6)
    preferred_bank = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=50)
    country = models.CharField(max_length=5, blank=True, null=True)
    bank_holder = models.CharField(max_length=30, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_account = models.CharField(max_length=50, null=True, blank=True)
    passcode = models.CharField(max_length=6, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_online = models.DateTimeField(auto_now=True, blank=True, null=True)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    feedback = models.DecimalField(max_digits=30, decimal_places=6, default=0)
    first_login = models.BooleanField(default=True)
    ic_no = models.CharField(max_length=50, null=True, blank=True)
    upload_ic = models.ImageField(upload_to = 'ic', null=True, blank=True)
    verified = models.BooleanField(default=False)
    upload_selfie = models.ImageField(upload_to = 'selfie', null=True, blank=True)
    bsb = models.CharField(max_length=50, null=True, blank=True)
    payid = models.CharField(max_length=50, null=True, blank=True)


class Tokens(models.Model):
    token = models.CharField(max_length=10)
    bid_usd = models.DecimalField(max_digits=30, decimal_places=6, default=0)
    ask_usd = models.DecimalField(max_digits=30, decimal_places=6, default=0)
    decimal_places = models.IntegerField(default=18)
    address = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)

class Ico(models.Model):
    token = models.CharField(max_length=10)
    issuer = models.CharField(max_length=255, null=True, blank=True)

class Currency(models.Model):
    country = models.CharField(max_length=5, default="my")
    currency = models.CharField(max_length=6)
    rate = models.DecimalField(max_digits=30, decimal_places=6, default=1)

class Offers(models.Model):
    offer_id = models.CharField(max_length=6)
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    country = models.CharField(max_length=5)
    trade_type = models.CharField(max_length=4, null=True)
    spread = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    maker = models.CharField(max_length=255, null=True)
    taker = models.CharField(max_length=255, null=True, blank=True)
    maximum = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    minimum = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    threshold = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    paymentwindow = models.IntegerField(default=15)
    maker_fees = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    fees = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    completed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True)
    cancelled = models.BooleanField(default=False)
    released = models.BooleanField(default=False)
    fiat = models.CharField(max_length=20, null=True, blank=True)
    transfer_txhash = models.CharField(max_length=255, null=True, blank=True)
    receive_txhash = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(decimal_places=0, max_digits=30, default=0)
    dispute = models.BooleanField(default=False)
    token = models.CharField(max_length=20, default="ETH")
    crypto = models.CharField(max_length=255, null=True, blank=True)
    verified_offer = models.BooleanField(default=False)
    go_fees = models.BooleanField(default=False)

class Wallet(models.Model):
    username = models.CharField(max_length=50)
    address = models.CharField(max_length=50, blank=True, null=True)
    balance = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    total_deposit=models.DecimalField(max_digits=50,decimal_places=0,default=0)
    referral_bonus=models.DecimalField(max_digits=30,decimal_places=0,default=0)
    last_redeemed = models.DateTimeField(auto_now=True)
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    referral_locked = models.BooleanField(default=True)

class Erc20Wallet(models.Model):
    username = models.CharField(max_length=50)
    address = models.CharField(max_length=50, blank=True, null=True)
    balance = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    total_deposit=models.DecimalField(max_digits=50,decimal_places=0,default=0)
    referral_bonus=models.DecimalField(max_digits=30,decimal_places=0,default=0)
    last_redeemed = models.DateTimeField(auto_now=True)
    tx_hash = models.CharField(max_length=255, null=True, blank=True)
    referral_locked = models.BooleanField(default=True)
    token = models.CharField(max_length=50, blank=True, null=True)

class Passcode(models.Model):
    email = models.EmailField(primary_key=True)
    passcode = models.CharField(max_length=6)

class BankReference(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=5,  blank=True, null=True)

class Conversation(models.Model):
    username = models.ForeignKey('self', on_delete=models.CASCADE)
    message = models.CharField(blank=True, null=True, max_length=225)
    status = models.CharField(blank=True, null=True, max_length=225)
    created_at = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    username = models.CharField(max_length=50, default=0)
    offer_id = models.CharField(max_length=6, null=True, blank=True)
    event = models.CharField(max_length=255, null=True, blank=True)
    
class BaseTxnFee(models.Model):
    last_updated = models.DateTimeField(auto_now=True)
    fee = models.DecimalField(max_digits=30, decimal_places=0, default=0)

class Referral(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    first_line = models.CharField(max_length=255, null=True, blank=True)
    second_line = models.CharField(max_length=255, null=True, blank=True)
    others_line = models.CharField(max_length=255, null=True, blank=True)
   
class OTC(models.Model): 
    name = models.CharField(max_length=255, null=True, blank=True)

class History(models.Model):
    username = models.CharField(max_length=255, null=True, blank=True)
    time = models.DateTimeField(auto_now=True, blank=True, null=True)
    activity = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    token = models.CharField(max_length=10) 
   
class Dividend(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=30, decimal_places=0, default=0)


class IEO_Sales(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=30, decimal_places=0, default=0)

class RICOGO(models.Model):
    security_code = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    member = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    referral = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    eth = models.DecimalField(max_digits=30, decimal_places=0, default=0)
    referer = models.BooleanField(default=False)
    ref_bonus = models.DecimalField(max_digits=30, decimal_places=0, default=0)
