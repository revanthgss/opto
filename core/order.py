import logging

from kiteconnect import KiteConnect
from requests.exceptions import ReadTimeout


class Order:
    def __init__(self, kite_instance: KiteConnect, order_id: int):
        self.order_id = None
        self.kite_instance = kite_instance
        order_data = kite_instance.order_history(order_id=order_id)[-1]
        for key, value in order_data.items():
            setattr(self, key, value)
        print(self.__dict__)

    def __str__(self):
        return self.order_id

    def modify(self, price: float = None, trigger_price: float = None, order_type: str = None):
        logging.info("Modifying order")
        print(price, trigger_price)
        new_order_id = self.kite_instance.modify_order(
            variety=KiteConnect.VARIETY_REGULAR,
            order_id=self.order_id,
            price=price,
            trigger_price=trigger_price,
            order_type=order_type,
        )
        return Order(self.kite_instance, new_order_id)

    def cancel(self):
        logging.info("Cancelling order")
        self.kite_instance.cancel_order(variety=KiteConnect.VARIETY_REGULAR, order_id=self.order_id)

    def get_status(self):
        try:
            latest_order_data = self.kite_instance.order_history(order_id=self.order_id)[-1]
            return latest_order_data.get('status')
        except ReadTimeout:
            return None


class TestOrder:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.symbol = self.tradingsymbol

    def modify(self, **kwargs):
        logging.info(
            f"Modifying order -> {self.tradingsymbol}-{self.price}-{self.trigger_price} -> {kwargs.get('price', None)} - {kwargs.get('trigger_price', None)}"
        )
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def cancel(self):
        logging.info(f"Cancelling order -> {self.tradingsymbol}-{self.price}-{self.trigger_price}")
