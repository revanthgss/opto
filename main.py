import logging
from datetime import datetime, date
from multiprocessing import set_start_method

from kiteconnect import KiteConnect

from constants import INSTRUMENT_SYMBOL, EXPIRY_DATE, ENTRY_TIME, EXIT_TIME, API_KEY, ACCESS_TOKEN, API_SECRET, LOTS
from core.strategy import StraddleStrategy

logging.basicConfig(level=logging.INFO)

kite = KiteConnect(api_key=API_KEY)

set_start_method("fork")


def gen_access_token():
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    print(f"Go to {kite.login_url()} and get the request token!!")
    REQUEST_TOKEN = input("Enter request token : ")
    data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
    print(data["access_token"])
    return data["access_token"]


access_token = gen_access_token()

logging.debug(f"Access Token - {access_token}")
kite.set_access_token(access_token)

entry_time = datetime.combine(date.today(), ENTRY_TIME)
exit_time = datetime.combine(date.today(), EXIT_TIME)


StraddleStrategy(
    kite_instance=kite, instrument_symbol=INSTRUMENT_SYMBOL, expiry_date=EXPIRY_DATE, access_token=access_token
).execute(entry_time=entry_time, exit_time=exit_time, n_lots=LOTS)
