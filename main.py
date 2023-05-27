import logging
from datetime import datetime, date
from multiprocessing import set_start_method

from kiteconnect import KiteConnect
from redis import Redis

from constants import INSTRUMENT_SYMBOL, ENTRY_TIME, EXIT_TIME, API_KEY, API_SECRET, LOTS
from core.strategy import StraddleStrategy
from utils import get_next_expiry

logging.basicConfig(level=logging.INFO)

cache = Redis()
kite = KiteConnect(api_key=API_KEY)

set_start_method("fork")


def gen_access_token():
    access_token = cache.get('kite:access_token')
    if access_token:
        return access_token.decode('utf-8')
    print(f"Go to {kite.login_url()} and get the request token!!")
    REQUEST_TOKEN = input("Enter request token : ")
    data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
    print(data["access_token"])
    cache.set('kite:access_token', data['access_token'], ex=43200)
    return data["access_token"]


access_token = gen_access_token()

logging.debug(f"Access Token - {access_token}")
kite.set_access_token(access_token)

entry_time = datetime.combine(date.today(), ENTRY_TIME)
exit_time = datetime.combine(date.today(), EXIT_TIME)
expiry_date = get_next_expiry().strftime("%Y-%m-%d")

StraddleStrategy(
    kite_instance=kite, instrument_symbol=INSTRUMENT_SYMBOL, expiry_date=expiry_date, access_token=access_token
).execute(entry_time=entry_time, exit_time=exit_time, n_lots=LOTS)
