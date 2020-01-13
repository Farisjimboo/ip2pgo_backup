import json
import web3

from django.conf import settings
from web3.auto.infura import w3

from web3 import Web3
from solc import compile_source
from web3.contract import Contract
from eth_account import Account

from directapp.models import UserProfile, Wallet, Offers

from infuraeth.contracts import (wallet_contract, escrow_contract)

def make_wallet (username):
    try:
        user_wallet = Wallet.objects.get(username = username)
    except Exception as e:
        Wallet.objects.create(username = username)
        user_wallet = Wallet.objects.get(username = username)
    
    arguments = wallet_contract
    try:
        contract_address, tx_hash, gas = make_contract(arguments)
    except Exception as e:
        return False
    
    user_wallet.address = contract_address
    user_wallet.save()
   
    return True

def make_escrow (offer_id):
    try:
        trade_offer = Offers.objects.get(offer_id = offer_id)
    except Exception as e:
        return False 
    
    try:
        buyer_wallet = Wallet.objects.get(username = trade_offer.buyer)
    except Exception as e:
        return False

    try:
        seller_wallet = Wallet.objects.get(username = trade_offer.seller)
    except Exception as e:
        return False

    arguments = escrow_contract
    arguments.constructors['buyer_address'] = buyer_wallet.address
    arguments.constructors['seller_address'] = seller_wallet.address

    try:
        contract_address, tx_hash, gas = make_contract(arguments)
    except Exception as e:
        return False

    trade_offer.escrow_creation_fee = gas * w3.eth.gasPrice
    trade_offer.escrow_address = contract_address
    trade_offer.save()

    return True

def make_contract (arguments):
    w3.eth.defaultAccount = Account.privateKeyToAccount(settings.INFURA_ETH_KEY).address
    nonce = w3.eth.getTransactionCount(w3.eth.defaultAccount)
    gasprice = w3.eth.gasPrice
    compiled_sol = compile_source(arguments.contract)
    contract_interface = compiled_sol['<stdin>:%s' % arguments.name]    
    Sol = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin'],
    )
    if arguments.constructors:
        deploy = Sol.constructor(**arguments.constructors).buildTransaction(
            dict(nonce=nonce, gasPrice=gasprice)
        )
    else:
        deploy = Sol.constructor().buildTransaction(
            dict(nonce=nonce, gasPrice=gasprice)
        )
    signed = w3.eth.account.signTransaction(deploy, settings.INFURA_ETH_KEY)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash, timeout=300)
    gas = tx_receipt.gasUsed
    #gas = w3.eth.estimateGas(deploy)
    address = tx_receipt.contractAddress
    
    return (address, tx_hash, gas)

