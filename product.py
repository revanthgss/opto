from kiteconnect import KiteConnect
import logging


class Product:

    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        self._kite_instance = kite_instance
        self.exchange = None
        self.variety = None
        self.trading_symbol = trading_symbol
        self.product = None
        self.validity = None

    def buy(self, quantity):
        logging.info(
            f"Placing a buy order of {self.trading_symbol} with quantity {quantity}")
        self._kite_instance.place_order(
            variety=self.variety,
            tradingsymbol=self.trading_symbol,
            exchange=self.exchange,
            transaction_type=KiteConnect.TRANSACTION_TYPE_BUY,
            order_type=KiteConnect.ORDER_TYPE_MARKET,
            quantity=quantity,
            product=self.product,
            disclosed_quantity=quantity,
            validity=self.validity
        )

    def sell(self, quantity):
        logging.info(
            f"Placing a sell order of {self.trading_symbol} with quantity {quantity}")
        self._kite_instance.place_order(
            variety=self.variety,
            tradingsymbol=self.trading_symbol,
            exchange=self.exchange,
            transaction_type=KiteConnect.TRANSACTION_TYPE_SELL,
            order_type=KiteConnect.ORDER_TYPE_MARKET,
            quantity=quantity,
            product=self.product,
            disclosed_quantity=quantity,
            validity=self.validity
        )

    def buy_limit(self, quantity, price):
        logging.info(
            f"Placing a buy limit order of {self.trading_symbol} with quantity {quantity} at {price}")
        self._kite_instance.place_order(
            variety=self.variety,
            tradingsymbol=self.trading_symbol,
            exchange=self.exchange,
            transaction_type=KiteConnect.TRANSACTION_TYPE_BUY,
            order_type=KiteConnect.ORDER_TYPE_LIMIT,
            quantity=quantity,
            product=self.product,
            disclosed_quantity=quantity,
            price=price,
            validity=self.validity
        )

    def sell_limit(self, quantity, price):
        logging.info(
            f"Placing a sell limit order of {self.trading_symbol} with quantity {quantity} at {price}")
        self._kite_instance.place_order(
            variety=self.variety,
            tradingsymbol=self.trading_symbol,
            exchange=self.exchange,
            transaction_type=KiteConnect.TRANSACTION_TYPE_SELL,
            order_type=KiteConnect.ORDER_TYPE_LIMIT,
            quantity=quantity,
            product=self.product,
            disclosed_quantity=quantity,
            price=price,
            validity=self.validity
        )


class Stock(Product):

    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        super().__init__(kite_instance, trading_symbol)
        self.exchange = KiteConnect.EXCHANGE_NSE
        self.variety = KiteConnect.VARIETY_REGULAR
        self.product = KiteConnect.PRODUCT_CNC
        self.validity = KiteConnect.VALIDITY_DAY


class Option(Product):

    def __init__(self, kite_instance: KiteConnect, trading_symbol):
        super().__init__(kite_instance, trading_symbol)
        self.exchange = KiteConnect.EXCHANGE_NFO
        self.variety = KiteConnect.VARIETY_REGULAR
        self.product = KiteConnect.PRODUCT_NRML
        self.validity = KiteConnect.VALIDITY_DAY
