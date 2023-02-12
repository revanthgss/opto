from typing import Union

from kiteconnect import KiteConnect
import logging
from redis import Redis
from constants import DRY_RUN
from order import Order, TestOrder

cache = Redis()


class Product:
    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        self._kite_instance = kite_instance
        self.exchange = None
        self.variety = None
        self.trading_symbol = trading_symbol
        self._product = None
        self.validity = None

    def get_order_type(self, price, trigger_price):
        if price:
            return KiteConnect.ORDER_TYPE_SL if trigger_price else KiteConnect.ORDER_TYPE_LIMIT
        else:
            return KiteConnect.ORDER_TYPE_SLM if trigger_price else KiteConnect.ORDER_TYPE_MARKET

    def _get_or_place_order(self, transaction_type, quantity, price=None, trigger_price=None):
        order_type = self.get_order_type(price, trigger_price)
        logging.info(
            f"Placing a {'buy' if transaction_type == KiteConnect.TRANSACTION_TYPE_BUY else 'sell'} order {self.trading_symbol}-{order_type} Price:{price} Trigger Price:{trigger_price}"
        )
        order_id = cache.get(f'{self.trading_symbol}{order_type}{KiteConnect.TRANSACTION_TYPE_BUY}').decode('utf-8')
        if order_id:
            return Order(self._kite_instance, order_id)
        order_id = self._kite_instance.place_order(
            variety=self.variety,
            tradingsymbol=self.trading_symbol,
            exchange=self.exchange,
            transaction_type=transaction_type,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            quantity=quantity,
            product=self._product,
            disclosed_quantity=quantity,
            validity=self.validity,
        )
        cache.set(f'{self.trading_symbol}{order_type}{transaction_type}', str(order_id), ex=43200)
        return Order(self._kite_instance, order_id)

    def buy(
        self,
        quantity,
        price=None,
        trigger_price=None,
    ) -> Union[Order, TestOrder]:
        return self._get_or_place_order(
            transaction_type=KiteConnect.TRANSACTION_TYPE_BUY,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
        )

    def sell(
        self,
        quantity,
        price=None,
        trigger_price=None,
    ) -> Union[Order, TestOrder]:
        return self._get_or_place_order(
            transaction_type=KiteConnect.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
        )


class Stock(Product):
    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        super().__init__(kite_instance, trading_symbol)
        self.exchange = KiteConnect.EXCHANGE_NSE
        self.variety = KiteConnect.VARIETY_REGULAR
        self._product = KiteConnect.PRODUCT_CNC
        self.validity = KiteConnect.VALIDITY_DAY


class Option(Product):
    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        super().__init__(kite_instance, trading_symbol)
        self.exchange = KiteConnect.EXCHANGE_NFO
        self.variety = KiteConnect.VARIETY_REGULAR
        self._product = KiteConnect.PRODUCT_MIS
        self.validity = KiteConnect.VALIDITY_DAY
