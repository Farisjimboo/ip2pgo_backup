import json, web3, random, requests
from django.conf import settings
from web3.auto.infura import w3
from django.utils.translation import ugettext_lazy as _
from web3 import Web3
from solc import compile_source
from web3.contract import Contract
from eth_account import Account
from decimal import Decimal
from directapp.models import UserProfile, Wallet, Offers, BaseTxnFee, Erc20Wallet, Tokens, History, IEO_Sales

from infuraeth.contracts import (
    wallet_contract,
    new_wallet_contract,
    erc20_contract,
    USDT_contract,
    OMG_contract,
    BTM_contract,
    ZRX_contract,
    SCC_contract,
    TUSD_contract,
    OneCity_contract,
    GO_contract,
    TEL_contract,
    TMB_contract,
    REGO_contract,
    PLS_contract,
    IRA_contract,
    pls_eth_contract,
    rego_eth_contract,
)
from django.utils import timezone
from datetime import timedelta
from time import sleep
from directapp import ieo

from .models import NonceManager

w3.eth.defaultAccount = Account.privateKeyToAccount(settings.INFURA_ETH_KEY).address
_gasprice = w3.eth.gasPrice + w3.toWei(1, 'gwei')
_test_escrow = '0xc754432a29095D0ac94a2d5B84E1dF183755d2cE'
_test_user = '0xc2Cbff7BeFB013C9518AbfAa5B1AcD9BC11869FE'
_test_second = settings.MAIN_WALLET


def get_nonce(nonce, estimate=False):
    prev_nonce = NonceManager.objects.all()
    if len(prev_nonce) == 0:
        NonceManager.objects.create(nonce=nonce)
        return nonce
   
    if not estimate: 
        if nonce <= prev_nonce[0].nonce:
            prev_nonce[0].nonce += 1
            prev_nonce[0].save()
            nonce = prev_nonce[0].nonce
        else:
            prev_nonce[0].nonce = nonce
            prev_nonce[0].save()

    return nonce


def contract_init(contract, address=None):
    compiled_sol = compile_source(contract.contract)
    contract_interface = compiled_sol['<stdin>:%s' % contract.name]

    if address:
        address = w3.toChecksumAddress(address)
        con = w3.eth.contract(
            address=address,
            abi=contract_interface['abi'],
        )
    else:
        con = w3.eth.contract(
            abi = contract_interface['abi'],
            bytecode = contract_interface['bin'],
        )

    return con


def contract_call(contract, function, address):
    interact = None
    con = contract_init(contract=contract, address=address)
  
    if 'deposit' in function:
        interact = con.functions.deposit()

    if 'getBalance' in function:
        interact = con.functions.getBalance(function['getBalance'])

    return interact


def trade_data_call(offer_id):
    offer = Offers.objects.get(offer_id=offer_id)
    trade_data = {}
    trade_data['amount'] = offer.amount
    trade_data['fiat'] = offer.fiat

    return trade_data


def contract_transact(contract, function, address, estimate=False):
    interact = None
    current_nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    nonce = get_nonce(current_nonce, estimate)
    txn = {
        'nonce': nonce,
        'gasPrice': _gasprice,
    }
 
    con = contract_init(contract=contract, address=address)

    if 'update' in function:
        interact = con.functions.update()

    if 'transfer' in function:
        interact = con.functions.transfer(function['transfer']['token'], function['transfer']['wallet'], function['transfer']['value'])

    if 'transfer_alt' in function:
        interact = con.functions.transfer_alt(function['transfer_alt']['token'], function['transfer_alt']['wallet'], function['transfer_alt']['value'])

    if 'transfer_token' in function:
        interact = con.functions.transfer(function['transfer_token']['wallet'], function['transfer_token']['value'])

    if interact:
        interact = interact.buildTransaction(txn)
        if estimate:
            retry = False
            return w3.eth.estimateGas(interact)
        else:
            signed = w3.eth.account.signTransaction(
                interact, settings.INFURA_ETH_KEY)
            tx_hash = None
            try:
                tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
            except Exception:
                tx_hash = None 
                nonce_revert = NonceManager.objects.all()[0]
                nonce_revert.nonce = nonce-1
                nonce_revert.save()

    return tx_hash

# must send in constructor kwargs
def contract_construct(contract, constructors=None, estimate=False):
    interact = None
    retry = True
    current_nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    nonce = get_nonce(current_nonce, estimate)

    txn = {
        'nonce': nonce,
        'gasPrice': _gasprice,
    }
    con = contract_init(contract=contract, address=None)

    if constructors:
        interact = con.constructor(**constructors)
    else:
        interact = con.constructor()

    if interact:
        interact = interact.buildTransaction(txn)
        if estimate:
            return w3.eth.estimateGas(interact)
        signed=w3.eth.account.signTransaction(interact,settings.INFURA_ETH_KEY)
        tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

        return tx_hash
    else:
        return None
 

def admin_transact(address, amount, estimate=False):
    current_nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    nonce = get_nonce(current_nonce, estimate)
    txn = {
        'nonce': nonce,
        'gasPrice': _gasprice,
        'gas': 200000,
        'to': address,
        'value': int(amount),
    }

    if estimate:
        return w3.eth.estimateGas(txn)
    signed = w3.eth.account.signTransaction(txn, settings.INFURA_ETH_KEY)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    return tx_hash


#transacting erc20 tokens requires their contracts to be available

#send in a dict
def create_user_wallet(username):
    # try to create new version of the wallet
    user_wallet = Wallet.objects.get(username=username)
    create = contract_construct(contract=wallet_contract)
    user_wallet.tx_hash = create.hex()
    user_wallet.save()    

    return True


def create_erc20_wallet(username):    
    erc20_wallet = Erc20Wallet.objects.filter(username=username)
    create_erc20 = contract_construct(contract=erc20_contract)
    tx = create_erc20.hex()
    for token in erc20_wallet:
        token.tx_hash = tx
        token.save()

    return True


#THIS FUNCTION IS TO BE CALLED MANUALLY ONLY
#create_ieo_wallet('user', 'PLS')
def create_ieo_wallet(username, token):
    user_wallet = Wallet.objects.get(username=username)
    wallet_contract = None

    if token == 'PLS':
        wallet_contract = pls_eth_contract
    elif token == 'REGO':
        wallet_contract = rego_eth_contract
    else:
        pass

    if wallet_contract:
        create = contract_construct(contract=wallet_contract)
        user_wallet.tx_hash = create.hex()
        user_wallet.save() 
    else:
        return False   

    return create.hex()


def get_eth_balance(address, ieotoken):
    deposit = 0
    retry = True

    if ieotoken == 'PLS':
        contract = pls_eth_contract
    elif ieotoken == 'REGO':
        contract = rego_eth_contract
    else:
        contract = wallet_contract

    while retry:
        try:
            deposit = contract_call(contract, 'deposit', address).call()
            retry = False
        except Exception:
            try:
                deposit = contract_call(contract, 'deposit', address).call()
                retry = False
            except Exception:
                pass

    deposit = Decimal(deposit)

    return deposit

# to deprecate or change. not actively used
def get_erc20_balance(username, amount, token):
    token_info = Tokens.objects.get(token=token)
    wallet = Erc20Wallet.objects.get(username=username, token=token)
    token_address = w3.toChecksumAddress(token_info.address)
    eth_info = Tokens.objects.get(token='ETH')
    non_pay_list = ['1CT', 'GO']
    tx_hash =  None    
    transfer_list = ['ZRX', 'BTM', 'SCC', 'TUSD', 'GO', 'TMB', 'REGO', 'PLS','iRA']
    if amount > 0:
        function = {'transfer': {'token': token_address, 'wallet': w3.eth.defaultAccount, 'value': int(amount)}}
        try:
            if token in transfer_list:
                tx_hash = contract_transact(erc20_contract, function, wallet.address)
            else:
                function = {'transfer_alt': {'token': token_address, 'wallet': w3.eth.defaultAccount, 'value': int(amount)}}
                tx_hash = contract_transact(erc20_contract, function, wallet.address)
        except Exception:
            return False

    return True

    
def withdraw(username, user_address, amount):
    wallet = Wallet.objects.get(username=username)
    to_address = w3.toChecksumAddress(user_address)
    fee = 0
    to_wallet = None

    user = UserProfile.objects.get(username=username)
    if user.verified: 
        fee = w3.toWei(0.005, 'ether')
    else:
        fee = w3.toWei(0.01, 'ether')

    if to_address == w3.eth.defaultAccount:
        return _(u"Test Withdrawal Successful!")

    try:
        to_wallet = Wallet.objects.get(address=to_address)
    except Exception:
        dup_wallet = Wallet.objects.filter(address=to_address)
        if len(dup_wallet) == 0:
            pass
        else:
            to_wallet = 'Duplicate'

    nett_amount = amount - fee

    if to_wallet and to_wallet != 'Duplicate' and to_wallet != wallet.address:
        to_wallet.balance += Decimal(nett_amount)
        to_wallet.save()
        History.objects.create(
            username = to_wallet.username,
            amount = nett_amount,
            token = 'ETH',
            activity = 'Deposit from %s' % (wallet.address),
        )           
        wallet.balance -= Decimal(amount)
        wallet.save()
        History.objects.create(
            username = username,
            amount = amount,
            token = 'ETH',
            activity = 'Withdrawal to %s' % (to_address),
        )           
        return _(u"Success")
    elif not to_wallet:
        tx_hash = admin_transact(to_address, nett_amount)
        if tx_hash:
            wallet.balance -= Decimal(amount)
            wallet.save()
            History.objects.create(
                username = username,
                amount = amount,
                token = 'ETH',
                activity = 'Withdrawal to %s, txhash: #%s' % (to_address, tx_hash.hex()),
            )           
            return tx_hash.hex()
        else:
            return False
    else:
        return False

# must get specific smart contracts in here and run contract_transact
def withdraw_erc20(username, user_address, amount, token):
    wallet = Erc20Wallet.objects.get(username=username, token=token)
    to_address = w3.toChecksumAddress(user_address)
    token_info = Tokens.objects.get(token=token)
    token_address = w3.toChecksumAddress(token_info.address)
    token_index = {
        'USDT': USDT_contract,
        'ZRX': ZRX_contract,
        'BTM': BTM_contract,
        'OMG': OMG_contract,
        'SCC': SCC_contract,
        'TUSD': TUSD_contract,
        '1CT': OneCity_contract,
        'GO': GO_contract,
        'TEL': TEL_contract,
        'TMB': TMB_contract,
        'REGO': REGO_contract,
        'PLS': PLS_contract,
        'iRA': IRA_contract,
    }
    non_pay_list = ['1CT', 'GO']
    gas_amount = None    
    token_contract = token_index[token]
    user = UserProfile.objects.get(username=username)
    fees = 0
    
    if user.verified:
        fees = 0.005
    else:
        fees = 0.01

    if token == 'PLS':
        fees = 0

    if to_address == w3.eth.defaultAccount:
        return _(u"Test Withdrawal Successful!")
    
    try: 
        to_wallet = Erc20Wallet.objects.get(address=to_address, token=token)
    except Exception:
        dup_wallet = Erc20Wallet.objects.filter(address=to_address, token=token)
        if len(dup_wallet) == 0:
            to_wallet = None
        else:
            to_wallet = 'Duplicate'
            
    eth = Tokens.objects.get(token='ETH')
    eth_mid = (eth.bid_usd + eth.ask_usd) / 2
    token_mid = (token_info.bid_usd + token_info.ask_usd) / 2
    token_per_eth = (eth_mid / token_mid)
    
    if to_wallet and to_wallet != 'Duplicate' and to_wallet != wallet.address:
        if token == 'GO' or token == 'PLS':
            fees = 0
        else:
            fees = (token_per_eth) * Decimal(fees * 10 ** token_info.decimal_places)

        to_wallet.balance += Decimal(amount) - Decimal(fees)
        to_wallet.save()
        History.objects.create(
            username = to_wallet.username,
            amount = amount - fees,
            token = token,
            activity ='Deposit from %s' % (wallet.address),
        )           

        wallet.balance -= Decimal(amount)
        wallet.save()
        History.objects.create(
            username = username,
            amount = amount,
            token = token,
            activity = 'Withdrawal to %s' % (to_address),
        )           
 
        return _(u"Success")
    elif not to_wallet:
        nett_amount = Decimal(amount) - (Decimal(fees) * Decimal(token_per_eth) * 10 ** token_info.decimal_places)
        try:
            tx_hash = contract_transact(token_contract, {'transfer_token':{'wallet':to_address, 'value':int(nett_amount)}}, token_address)
        except Exception:
            return False

        if tx_hash:
            wallet.balance -= Decimal(amount)
            wallet.save()
            History.objects.create(
                username = username,
                amount = amount,
                token = token,
                activity = 'Withdrawal to: %s, txhash: #%s' % (to_address, tx_hash.hex()),
            )           

        return tx_hash.hex()
    else:
        return False


def take_trade(offer_id, trade_data):
    offer = Offers.objects.get(offer_id=offer_id)
    
    #mid_go = (go_data.bid_usd + go_data.ask_usd) / 2
    #mid_token = (token_data.bid_usd + token_data.ask_usd) / 2
   # go_fee is 90%
   # go_fee = (mid_token / mid_go) * (offer.fees / 10 ** token_data.decimal_places) * 0.9
    #go_fee = Decimal(go_fee * 10 ** go_data.decimal_places)
    
    amount = Decimal(trade_data['amount'])
    offer.amount = amount
    offer.fiat = trade_data['fiat']
    if offer.crypto == 'GO' or offer.token == 'GO':
        offer.fees = 0
    elif offer.crypto == 'TUSD' or offer.crypto == 'ETH':
        offer.fees = amount * 2 / 1000
    else: 
        offer.fees = amount * 8 / 1000

    if offer.token == 'PLS' and offer.crypto == 'ETH':
        offer.fees = amount * 8 / 1000   

    offer.save()
  
    if offer.token == 'ETH':
        maker_wallet = Wallet.objects.get(username=offer.maker)
        taker_wallet = Wallet.objects.get(username=offer.taker)
    else:
        maker_wallet = Erc20Wallet.objects.get(username=offer.maker, token=offer.token)
        taker_wallet = Erc20Wallet.objects.get(username=offer.taker, token=offer.token)
    
    if offer.trade_type == 'sell':
        maker_wallet.balance -= amount
        maker_wallet.save()
        History.objects.create(
            username = maker_wallet.username,
            amount = amount,
            token = offer.token,
            activity ='In escrow %s. Offer #%s' % (offer.token, offer.offer_id),
        )           
    elif offer.trade_type == 'buy':
        taker_wallet.balance -= amount
        taker_wallet.save()
        History.objects.create(
            username = taker_wallet.username,
            amount = amount - offer.fees,
            token = offer.token,
            activity ='In escrow %s. Offer #%s' % (offer.token, offer.offer_id),
        )           
    return True


def release(offer_id):
    offer = Offers.objects.get(offer_id=offer_id)
    go_data = Tokens.objects.get(token='GO')
    token_data = Tokens.objects.get(token=offer.token)
    
    mid_go = (go_data.bid_usd + go_data.ask_usd) / 2
    mid_token = (token_data.bid_usd + token_data.ask_usd) / 2
    # go_fee is 90%
    #go_fee = (mid_token / mid_go) * (offer.fees / 10 ** token_data.decimal_places) * 0.9
    #go_fee = Decimal(go_fee * 10 ** go_data.decimal_places)

    if offer.token == 'ETH':
        taker_wallet = Wallet.objects.get(username=offer.taker)
        maker_wallet = Wallet.objects.get(username=offer.maker)
        amount = offer.amount
   
        if offer.trade_type == 'sell':
            """
            if offer.go_fees:
                offer.fees = 0
                ercwallet = Erc20Wallet.objects.get(username=offer.taker, token='GO')
                ercwallet -= go_fee
                ercwallet.save()
                History.objects.create(
                    username = taker_wallet.username,
                    amount = go_fee,
                    token = 'GO',
                    activity='Fee paid with GO. Offer #%s' % (offer.offer_id),
                )           
             """   
            check_history = History.objects.filter(activity__contains=offer.offer_id, username=taker_wallet.username)
            if len(check_history) == 0:   
                taker_wallet.balance += amount - offer.fees
                taker_wallet.save()
                History.objects.create(
                    username = taker_wallet.username,
                    amount = amount - offer.fees,
                    token = offer.token,
                    activity='Bought %s. Offer #%s' % (offer.token, offer.offer_id),
                )           
                escrow_history = None
                try:
                    escrow_history = History.objects.get(username = maker_wallet.username, activity__contains=offer.offer_id)
                except Exception:
                    escrow_history = History.objects.filter(username = maker_wallet.username, activity__contains=offer.offer_id)
                    escrow_history = escrow_history[0]
                if escrow_history:
                    escrow_history.activity='Sold %s. Offer #%s' % (offer.token, offer.offer_id)
                    escrow_history.save()
                offer.released = True
                offer.save()

        elif offer.trade_type == 'buy':
            check_history = History.objects.filter(activity__contains=offer.offer_id, username=maker_wallet.username)
            if len(check_history) == 0:
                if offer.crypto == 'TUSD' or offer.crypto == 'ETH':
                    maker_wallet.balance += amount - offer.fees
                else:
                    maker_wallet.balance += amount
                maker_wallet.save()
                History.objects.create(
                    username = maker_wallet.username,
                    amount = amount,
                    token = offer.token,
                    activity='Bought %s. Offer #%s' % (offer.token, offer.offer_id),
                )  
                escrow_history = None
                try:
                    escrow_history = History.objects.get(username = taker_wallet.username, activity__contains=offer.offer_id)
                except Exception:
                    escrow_history = History.objects.filter(username = taker_wallet.username, activity__contains=offer.offer_id)
                    escrow_history = escrow_history[0]
                if escrow_history:
                    escrow_history.activity='Sold %s. Offer  #%s' % (offer.token, offer.offer_id)
                    escrow_history.save()
                offer.released = True
                offer.save()

    else:
        taker_Erc20wallet = Erc20Wallet.objects.get(username=offer.taker, token=offer.token)
        maker_Erc20wallet = Erc20Wallet.objects.get(username=offer.maker, token=offer.token)
        amount = offer.amount

        if offer.trade_type == 'sell':
            check_history = History.objects.filter(activity__contains=offer.offer_id, username=taker_Erc20wallet.username)
            if len(check_history) == 0:
                taker_Erc20wallet.balance += amount - offer.fees
                taker_Erc20wallet.save()
                History.objects.create(
                    username = taker_Erc20wallet.username,
                    amount = amount - offer.fees,
                    token = offer.token,
                    activity='Bought %s. Offer #%s' % (offer.token, offer.offer_id),
                )
                escrow_history = None
                try:
                    escrow_history = History.objects.get(username = maker_Erc20wallet.username, activity__contains=offer.offer_id)
                except Exception:
                    escrow_history = History.objects.filter(username = maker_Erc20wallet.username, activity__contains=offer.offer_id)
                    escrow_history = escrow_history[0]
                if escrow_history:
                    escrow_history.activity='Sold %s. Offer  #%s' % (offer.token, offer.offer_id)
                    escrow_history.save()
                offer.released = True
                offer.save()

        elif offer.trade_type == 'buy':
            check_history = History.objects.filter(activity__contains=offer.offer_id, username=maker_Erc20wallet.username)
            if len(check_history) == 0:
                if offer.crypto == 'TUSD' or offer.crypto == 'ETH':
                    maker_Erc20wallet.balance += amount - offer.fees
                else:
                    maker_Erc20wallet.balance += amount
                maker_Erc20wallet.save()
                History.objects.create(
                    username = maker_Erc20wallet.username,
                    amount = amount,
                    token = offer.token,
                    activity='Bought %s. Offer #%s' % (offer.token, offer.offer_id),
                )
                escrow_history = None
                try:
                    escrow_history = History.objects.get(username = taker_Erc20wallet.username, activity__contains=offer.offer_id)
                except Exception:
                    escrow_history = History.objects.filter(username = taker_Erc20wallet.username, activity__contains=offer.offer_id)
                    escrow_history = escrow_history[0]
                if escrow_history:
                    escrow_history.activity='Sold %s. Offer  #%s' % (offer.token, offer.offer_id)
                    escrow_history.save()
                offer.released = True
                offer.save()

    return True


def cancel(offer_id):
    offer = Offers.objects.get(offer_id=offer_id)
    
    if offer.token == 'ETH':
        maker_wallet = Wallet.objects.get(username=offer.maker)
        taker_wallet = Wallet.objects.get(username=offer.taker)

    else:
        maker_wallet = Erc20Wallet.objects.get(username=offer.maker, token=offer.token)
        taker_wallet = Erc20Wallet.objects.get(username=offer.taker, token=offer.token)

    amount = offer.amount

    if offer.trade_type == 'sell':
        maker_wallet.balance += amount
        maker_wallet.save()
        History.objects.create(
            username = maker_wallet.username,
            amount = amount,
            token = offer.token,
            activity='Cancel remittance Offer %s' % (offer.offer_id),
        )           

        taker_wallet.balance -= offer.fees
        taker_wallet.save()
        History.objects.create(
            username = taker_wallet.username,
            amount = offer.fees,
            token = offer.token,
            activity='Cancel penalty Offer %s' % (offer.offer_id),
        )           

    elif offer.trade_type == 'buy':
        taker_wallet.balance += amount + offer.fees
        taker_wallet.save()
        History.objects.create(
            username = taker_wallet.username,
            amount = amount + offer.fees,
            token = offer.token,
            activity='Cancel remittance Offer %s' % (offer.offer_id),
        )           

        maker_wallet.balance -= offer.fees
        maker_wallet.save()
        History.objects.create(
            username = maker_wallet.username,
            amount = offer.fees,
            token = offer.token,
            activity='Cancel penalty Offer %s' % (offer.offer_id),
        )           

    return True
