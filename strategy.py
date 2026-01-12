from collections import deque
import statistics

class MeanReversionStrategy:
    def __init__(self, symbol, window_size=20):

        self.symbol = symbol
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

        #State variables
        self.current_sma = None
        self.latest_price = None

    def on_tick(self, price):
        self.latest_price=float(price)
        self.history.append(self.latest_price)

        #default
        result = {
            "symbol": self.symbol,
            "price": self.latest_price,
            "sma": None,
            "signal": "WAITING_FOR_DATA",
            "is_hot": False # for frontend
        }

        #check for enough data
        if len(self.history) < self.window_size:
            return result
        
        #calculate indicators
        self.current_sma = statistics.mean(self.history)
        result["sma"] = round(self.current_sma, 2)

        #generate signal
        #threshold: .5% deviation from avg
        upper_band = self.current_sma * 1.005
        lower_band = self.current_sma * 0.995

        if self.latest_price < lower_band:
            result["signal"] = "BUY"
            result['is_hot'] = True
        elif self.latest_price > upper_band:
            result['signal'] = "SELL"
            result["is_hot"] = True
        else:
            result["signal"] = "HOLD"
        return result