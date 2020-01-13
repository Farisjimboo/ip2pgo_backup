import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import UserProfile, Erc20Wallet, Wallet
from web3.auto.infura import w3

all_erc20 = Erc20Wallet.objects.filter(token='GO', tx_hash__isnull=False, address__isnull=True)

for erc20 in all_erc20:
    add = w3.eth.getTransactionReceipt(erc20.tx_hash)
    user_erc20 = Erc20Wallet.objects.filter(username=erc20.username)
    for each_token in user_erc20:
        each_token.address = add.contractAddress
        each_token.save()

all_wallet = Wallet.objects.filter(tx_hash__isnull=False, address__isnull=True)

for wallet in all_wallet:
    add = w3.eth.getTransactionReceipt(wallet.tx_hash)
    wallet.address = add.contractAddress
    wallet.save()
~                                                                                                                                                                       ~                                                                                                                                                                       ~                        
