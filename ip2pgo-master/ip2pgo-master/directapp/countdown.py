from django.contrib.sessions.middleware import SessionMiddleware
from .models import Trades
from datetime import datetime, timedelta
import time

def countdown(offer_id):
    trade = Trades.objects.get(offer_id=offer_id)
    start = trade.startTrade
    end = trade.endTrade

    while datetime.utcnow() < end:
        time.sleep(0.99)
        minute, second = divmod((end - datetime.utcnow()).seconds, 60)
        if second < 10:
            second = "0%s" % second
        return "%s:%s" % (minute, second)
