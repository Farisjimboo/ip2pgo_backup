from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from directapp.models import UserProfile, Offers
import random, string, requests
import smtplib
from .forms import UploadForm
from infuraeth import interface
from .engine import upload_file_handler, create_session

def initiate_dispute(requests, offer_id):
    create = create_session(offer_id)
    """
    if create:
        # send a signal here, prompting buyer_proof and seller_proof
    else:
        # no idea how to handle the exception, must be something and can't leave it hanging. also can't potentially make a non-ending loop.
    """
def buyer_proof(requests, offer_id):
    trade = Offers.objects.get(offer_id=offer_id)
    buyer = trade.buyer
    if 'upload' in request.POST:
        uploadform = UploadForm(request.POST, request.FILES)
        handle_file(request.FILES['file'])
        # signal should be here
    else:
        uploadform = UploadForm()

def seller_proof(requests, offer_id):
    trade = Offers.objects.get(offer_id=offer_id)
    seller = trade.buyer
    if 'upload' in request.POST:
        uploadform = UploadForm(request.POST, request.FILES)
        handle_file(request.FILES['file'])
        # signal should be here
    else:
        uploadform = UploadForm()

def conclude_buyer(requests, offer_id):
    trade = Offers.objects.get(offer_id=offer_id)
    buyer = trade.buyer

def conclude_seller(requests, offer_id):
    trade = Offers.objects.get(offer_id=offer_id)
    seller = trade.seller


