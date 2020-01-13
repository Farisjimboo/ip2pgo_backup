from django.db import models


class AdminProfile(models.Model):

    admin_name = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    clearance = models.CharField(max_length=10, default='admin')
