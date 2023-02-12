from datetime import time, datetime

ACCESS_TOKEN = "Ge600JTEBtbsXPAu9180vjTxFUFDQA1u"
API_KEY = "dssjo6h86cvvi68m"
API_SECRET = "fofn2rkph7wi9gl3un0xy8xf4if20s2s"


STOP_LOSS = 40
STOP_LOSS_TRAILING_TRIGGER = 10
TARGET = 50
ADD_TARGETS = False
MINIMUM_QUANTITY = 25
LOTS = 4

INSTRUMENT_SYMBOL = 'BANKNIFTY'
INSTRUMENT_SYMBOL_NAME = 'NIFTY BANK'
EXPIRY_DATE = '2023-02-16'

expiry_date = datetime.strptime(EXPIRY_DATE, '%Y-%m-%d')
EXPIRY_DATE_STRING = f'{expiry_date.year%100}{expiry_date.month}{expiry_date.day:02d}'

DRY_RUN = False

ENTRY_TIME = time(9, 29, 30)
EXIT_TIME = time(14, 59, 30)
