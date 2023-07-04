import logging
from datetime import datetime, date
from typing import List, Dict, Iterable, Tuple, Optional
from redis import Redis

from kiteconnect import KiteConnect
from option_chain_stream import OptionChain

from constants import (
    STOP_LOSS,
    MINIMUM_QUANTITY,
    STOP_LOSS_TRAILING_TRIGGER,
    API_KEY,
    API_SECRET,
    INSTRUMENT_SYMBOL_NAME,
    ENTRY_TIME,
    TARGET,
    ADD_TARGETS,
)
from core.order import Order
from core.product import Option
from utils import get_expiry_date_string


cache = Redis()

class StraddleStrategy:
    name = 'straddle-strategy'

    def __init__(
        self,
        kite_instance: KiteConnect,
        instrument_symbol: str,
        expiry_date: str,
        access_token: str,
    ):
        self.n_lots = 1
        self.kite_instance = kite_instance
        self.instrument_symbol = instrument_symbol
        option_chain = OptionChain(
            symbol=instrument_symbol,
            expiry=expiry_date,
            api_key=API_KEY,
            api_secret=API_SECRET,
            access_token=access_token,
            underlying=True,
        )
        if datetime.now() < datetime.combine(date.today(), ENTRY_TIME):
            option_chain.sync_instruments()
        self.stream = option_chain.create_option_chain()
        self._option_orders = {"CE": None, "PE": None}  # type: Dict[str, Optional[Order]]
        self._stop_loss_orders = {"CE": None, "PE": None}  # type: Dict[str, Optional[Order]]
        self._target_orders = {"CE": None, "PE": None}  # type: Dict[str, Optional[Order]]
        self._init_orders()
        self._stop_losses = {"PE": 0.0, "CE": 0.0}
        self._targets = {"PE": 0.0, "CE": 0.0}
        self._put_profit = 0
        self._call_profit = 0
        self.token_list = None

    def _init_orders(self):
        sell_ce = cache.get(f'STRATVAR:{self.name}:SELL_CE')
        sl_ce = cache.get(f'STRATVAR:{self.name}:SL_CE')
        sell_pe = cache.get(f'STRATVAR:{self.name}:SELL_PE')
        sl_pe = cache.get(f'STRATVAR:{self.name}:SL_PE')
        if sell_ce:
            self._option_orders["CE"] = Order(self.kite_instance, sell_ce.decode('utf-8'))
        if sl_ce:
            self._stop_loss_orders["CE"] = Order(self.kite_instance, sl_ce.decode('utf-8'))
        if sell_pe:
            self._option_orders["PE"] = Order(self.kite_instance, sell_pe.decode('utf-8'))
        if sl_pe:
            self._stop_loss_orders["PE"] = Order(self.kite_instance, sl_pe.decode('utf-8'))

    @property
    def profit(self):
        return (self._call_profit + self._put_profit) * self.n_lots * MINIMUM_QUANTITY

    def get_token_dictionary(self, option_chain: List[Dict]) -> Iterable[Dict]:
        expiry_date_string = get_expiry_date_string()
        print(expiry_date_string)
        processed_token_list = []
        for option in option_chain:
            token = option["symbol"]
            if token != INSTRUMENT_SYMBOL_NAME:
                processed_token_list.append(
                    {
                        "symbol": token,
                        "strike_price": token.split(expiry_date_string)[-1][:-2],
                        "instrument_type": "PUT" if token[-2:] == "PE" else "CALL",
                    }
                )
        return processed_token_list

    def get_current_price(self, symbol: str, option_chain: List[Dict]) -> float:
        return next(filter(lambda instrument: instrument["symbol"] == symbol, option_chain))['last_price']

    def find_nearest_options(self, price: float, option_chain: List[Dict]) -> Tuple[Dict, Dict]:
        sorted_token_list = sorted(self.token_list, key=lambda token: abs(float(token["strike_price"]) - price))
        nearest_call_option = next(
            filter(
                lambda instrument: instrument["symbol"] == sorted_token_list[1]["symbol"][:-2] + "CE",
                option_chain,
            )
        )
        nearest_put_option = next(
            filter(
                lambda instrument: instrument["symbol"] == sorted_token_list[1]["symbol"][:-2] + "PE",
                option_chain,
            )
        )
        return nearest_call_option, nearest_put_option

    def exit_trades(self):
        print("Exiting trades", self._stop_loss_orders["CE"], self._stop_loss_orders["PE"])
        if self._stop_loss_orders["CE"]:
            self._stop_loss_orders["CE"].modify(order_type=KiteConnect.ORDER_TYPE_MARKET)
        if self._target_orders["CE"]:
            self._target_orders["CE"].cancel()
        if self._stop_loss_orders["PE"]:
            self._stop_loss_orders["PE"].modify(order_type=KiteConnect.ORDER_TYPE_MARKET)
        if self._target_orders["PE"]:
            self._target_orders["PE"].cancel()

    def monitor_triggers(self, option_chain: List[Dict]):
        # This condition occurs when both call and put orders are pending
        # Here we will check if any stop loss has hit and mark the respective order as None
        current_call_option_premium = self.get_current_price(self._option_orders["CE"].tradingsymbol, option_chain)
        current_put_option_premium = self.get_current_price(self._option_orders["PE"].tradingsymbol, option_chain)
        print(
            f"Profit : {round(MINIMUM_QUANTITY*self.n_lots*(self._option_orders['PE'].average_price+self._option_orders['CE'].average_price-current_put_option_premium-current_call_option_premium),2)}"
        )
        if self._stop_loss_orders["PE"] and self._stop_loss_orders["PE"].get_status() == 'COMPLETE':
            logging.info("Stop loss hit for PUT")
            self._stop_loss_orders["PE"] = None
            if self._target_orders["PE"]:
                self._target_orders["PE"].cancel()
        elif self._stop_loss_orders["CE"] and self._stop_loss_orders["CE"].get_status() == 'COMPLETE':
            logging.info("Stop loss hit for CALL")
            self._stop_loss_orders["CE"] = None
            if self._target_orders["PE"]:
                self._target_orders["PE"].cancel()

    def entry(self, option_chain):
        n_lots = self.n_lots
        self.token_list = self.get_token_dictionary(option_chain)
        # Ideally this should occur only once at the start of the day
        underlying_stock_price = self.get_current_price(INSTRUMENT_SYMBOL_NAME, option_chain)
        nearest_call_option, nearest_put_option = self.find_nearest_options(underlying_stock_price, option_chain)
        print('Underlying -- ', nearest_call_option, nearest_put_option)
        self._option_orders["CE"] = Option(self.kite_instance, nearest_call_option["symbol"]).sell(
            n_lots * MINIMUM_QUANTITY
        )
        self._option_orders["PE"] = Option(self.kite_instance, nearest_put_option["symbol"]).sell(
            n_lots * MINIMUM_QUANTITY
        )
        # Store stop losses
        self._stop_losses["CE"] = round(
            0.05 * int(nearest_call_option["last_price"] * (1 + STOP_LOSS / 100) / 0.05), 2
        )
        self._stop_losses["PE"] = round(
            0.05 * int(nearest_put_option["last_price"] * (1 + STOP_LOSS / 100) / 0.05), 2
        )
        # Keep stop loss orders
        self._stop_loss_orders["CE"] = Option(self.kite_instance, nearest_call_option["symbol"]).buy(
            n_lots * MINIMUM_QUANTITY, price=self._stop_losses["CE"] + 2, trigger_price=self._stop_losses["CE"]
        )
        self._stop_loss_orders["PE"] = Option(self.kite_instance, nearest_put_option["symbol"]).buy(
            n_lots * MINIMUM_QUANTITY, price=self._stop_losses["PE"] + 2, trigger_price=self._stop_losses["PE"]
        )
        cache.set(f'STRATVAR:{self.name}:SELL_CE', self._option_orders["CE"].order_id, ex=43200)
        cache.set(f'STRATVAR:{self.name}:SL_CE', self._stop_loss_orders["CE"].order_id, ex=43200)
        cache.set(f'STRATVAR:{self.name}:SELL_PE', self._option_orders["PE"].order_id, ex=43200)
        cache.set(f'STRATVAR:{self.name}:SL_PE', self._stop_loss_orders["PE"].order_id, ex=43200)
        if ADD_TARGETS:
            self._targets["CE"] = round(0.05 * int(nearest_call_option["last_price"] * (1 - TARGET / 100) / 0.05), 2)
            self._targets["PE"] = round(0.05 * int(nearest_put_option["last_price"] * (1 - TARGET / 100) / 0.05), 2)
            # Keep target orders
            self._target_orders["CE"] = Option(self.kite_instance, nearest_call_option["symbol"]).buy(
                n_lots * MINIMUM_QUANTITY,
                price=self._targets["CE"] + 2,
                trigger_price=self._targets["CE"],
            )
            self._target_orders["PE"] = Option(self.kite_instance, nearest_put_option["symbol"]).buy(
                n_lots * MINIMUM_QUANTITY,
                price=self._targets["PE"] + 2,
                trigger_price=self._targets["PE"],
            )

    def execute(self, entry_time: datetime, exit_time: datetime, n_lots: int = 1):
        self.n_lots = n_lots
        started = False
        for idx, option_chain in enumerate(self.stream):
            current_time = datetime.now()
            if current_time < entry_time:
                print("Waiting for entry time!!")
                continue
            if current_time >= exit_time or (
                started and self._stop_loss_orders["CE"] is None and self._stop_loss_orders["PE"] is None
            ):
                print("Time to exit the trade")
                self.exit_trades()
                return
            started = True
            if self._option_orders["CE"] is None and self._option_orders["PE"] is None:
                self.entry(option_chain)
            else:
                # This will occur when either call or put order hits the stop loss
                # Here we try to decrease stop loss for every 10% fall
                if self._stop_loss_orders["CE"] is None or self._stop_loss_orders["PE"] is None:
                    instrument_type = "CE" if self._stop_loss_orders["CE"] else "PE"
                    current_stop_loss_order = self._stop_loss_orders[instrument_type]
                    current_stop_loss = self._stop_losses[instrument_type]
                    option_premium = self.get_current_price(current_stop_loss_order.tradingsymbol, option_chain)
                    print(
                        option_premium,
                        (current_stop_loss * (1 - STOP_LOSS_TRAILING_TRIGGER / 100)) / (1 + STOP_LOSS / 100),
                    )
                    if option_premium <= (current_stop_loss * (1 - STOP_LOSS_TRAILING_TRIGGER / 100)) / (
                        1 + STOP_LOSS / 100
                    ):
                        # Reduce the stop loss order price
                        new_stop_loss = round(0.05*int(option_premium * (1 + STOP_LOSS / 100)/0.05), 2)
                        self._option_orders[instrument_type] = current_stop_loss_order.modify(
                            price=new_stop_loss + 2, trigger_price=new_stop_loss
                        )
                        self._stop_losses[instrument_type] = new_stop_loss
                    self.monitor_triggers(option_chain)
                else:
                    self.monitor_triggers(option_chain)
                    if self._stop_loss_orders["CE"] is None or self._stop_loss_orders["PE"] is None:
                        instrument_type = "CE" if self._stop_loss_orders["CE"] else "PE"
                        current_stop_loss_order = self._stop_loss_orders[instrument_type]
                        option_premium = self.get_current_price(current_stop_loss_order.tradingsymbol, option_chain)
                        new_stop_loss = round(0.05*int(option_premium * (1 + STOP_LOSS / 100)/0.05), 2)
                        print(new_stop_loss)
                        self._option_orders[instrument_type] = current_stop_loss_order.modify(
                            price=new_stop_loss + 2, trigger_price=new_stop_loss
                        )
                        self._stop_losses[instrument_type] = new_stop_loss


# HK7058
# 9@Revanth
# 533201
