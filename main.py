import logging
from kiteconnect import KiteConnect
from product import Stock, Option

API_KEY = "dssjo6h86cvvi68m"
API_SECRET = "fofn2rkph7wi9gl3un0xy8xf4if20s2s"

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=API_KEY)

ACCESS_TOKEN = "RNyX5SF14aUrJ0QJA01vcKonG9FsZK9A"


def gen_access_token():
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    print(f'Go to {kite.login_url()} and get the request token!!')
    REQUEST_TOKEN = input("Enter request token : ")
    data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
    return data["access_token"]


access_token = gen_access_token()

logging.debug(f'Access Token - {access_token}')
kite.set_access_token(access_token)
