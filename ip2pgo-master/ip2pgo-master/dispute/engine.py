from dispute.models import DisputeSession 
from directapp.models import Wallet, Offers
#from infuraeth.interface import resolve_dispute 

from datetime import datetime

def create_session(offer_id):
    trade = Offers.objects.get(offer_id=offer_id)
    trade.dispute = True
    trade.save()

    check_session = DisputeSession.objects.filter(offer_id=offer_id)

    if len(check_session) == 0: 
        Session.objects.create(
            offer_id = offer_id,
            buyer = trade.buyer,
            seller = trade.seller,
        )
    else:
        pass

    session = DisputeSession.objects.get(trade=offer_id)
    offer_id = session.offer_id

    return offer_id

def resolve_session(offer_id, username):
    session = DisputeSession.objects.get(offer_id = offer_id)
    session.verdict = username
    session.status = 'Resolved'
    session.end_dispute = datetime.utcnow()
    session.save()
  
    try: 
        resolve_dispute(session.trade, session.verdict)
    except Exception as e:
        return False

    return True

def upload_file_handler(offer_id, username, filename):
    session = DisputeSession.objects.get(offer_id = offer_id)
    
    if username == session.buyer:
        try:
            session.buyer_doc.user_directory_path(session, filename)
        except Exception as e:
            return False
    elif username == session.seller:
        try:
            session.seller_doc.user_directory_path(session, filename)
        except Exception as e:
            return False
    else:
        return False

    session.save()

    return True

def approve_buyer_proof(offer_id):
    session = DisputeSession.objects.get(offer_id = offer_id)
    session.buyer_doc_approve = True
    session.save()

    return True

def approve_seller_proof(offer_id):
    session = DisputeSession.objects.get(offer_id = offer_id)
    session.seller_doc_approve = True
    session.save()

    return True

