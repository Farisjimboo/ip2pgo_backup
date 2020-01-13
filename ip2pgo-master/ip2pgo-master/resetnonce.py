import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from infuraeth.models import NonceManager

"""
This script is run daily
"""
nm = NonceManager.objects.all()
nm = nm[0]
nm.nonce = 0
nm.save()
