from datetime import datetime, timedelta


def get_next_expiry():
    today = datetime.now() + timedelta(days=2)
    days_to_next_thursday = (3 - today.weekday()) % 7
    next_thursday = today + timedelta(days=days_to_next_thursday)
    return next_thursday


def get_option_symbol(instrument_symbol, price, is_call, expiry_date=None):
    if expiry_date is None:
        expiry_date = get_next_expiry()
    print(expiry_date)
    is_last_expiry_of_month = (expiry_date + timedelta(days=7)).month != expiry_date.month
    expiry_date_string = (
        expiry_date.strftime('%y%m%d') if not is_last_expiry_of_month else expiry_date.strftime('%y%b').upper()
    )
    suffix = 'CE' if is_call else 'PE'
    if isinstance(price, (int, float)):
        price = str((int(price + 50) // 100) * 100)
    return f'{instrument_symbol}{expiry_date_string}{price}{suffix}'

