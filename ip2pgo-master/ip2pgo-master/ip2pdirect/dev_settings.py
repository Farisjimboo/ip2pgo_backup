from django.conf import settings 
 
DEBUG = True 

ALLOWED_HOSTS = ['*']
DATABASES = settings.DATABASES 
DATABASES['default'] = {'ENGINE':'django.db.backends.sqlite3', 'NAME':'/home/faris/work/ip2pdirect/ip2pdirect/ip2pdb'}

""" 
ALLOWED_HOSTS = ['*']
DATABASES = settings.DATABASES 
DATABASES['default']['NAME'] = 'ip2pdirect' 
DATABASES['default']['HOST'] = 'rm-zf8flfa599aj137d8.mysql.kualalumpur.rds.aliyuncs.com' 
DATABASES['default']['USER'] = 'ip2pdirect'
DATABASES['default']['PASSWORD'] = 'Gamingsince333' 
"""
