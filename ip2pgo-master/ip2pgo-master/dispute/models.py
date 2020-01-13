from django.db import models

class DisputeSession(models.Model):
    #def user_directory_path(instance, filename):
    #    return 'dispute_uploads/%s/filename' % (instance.order_id, filename) 

    offer_id = models.CharField(max_length=6)
    start_dispute = models.DateTimeField(auto_now_add=True)
    end_dispute = models.DateTimeField(null=True, )
    taker_doc = models.ImageField(upload_to='dispute', null=True, blank=True)
    taker_doc_approve = models.BooleanField(default=False)
    maker_doc = models.ImageField(upload_to='dispute', null=True, blank=True)
    maker_doc_approve = models.BooleanField(default=False)
    buyer_extension = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='New')
    verdict = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=5, default='my')
    admin = models.CharField(max_length=255, null=True, blank=True)
    upload_ss = models.ImageField(upload_to = 'ss', null=True, blank=True)

class DisputeChat(models.Model):
    offer_id = models.CharField(max_length=6)
    talker = models.CharField(max_length=255, null=True, blank=True)
    message = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True) 
