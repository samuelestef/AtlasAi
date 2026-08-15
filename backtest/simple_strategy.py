"""
Atlas AI
Simple Strategy
"""

from backtesting import Strategy


class AtlasStrategy(Strategy):

    def init(self):
        pass

    def next(self):

        close = self.data.Close[-1]

        ema50 = self.data.EMA50[-1]

        ema200 = self.data.EMA200[-1]

        rsi = self.data.RSI[-1]

        atr = self.data.ATR[-1]

        if self.position:
            return

        if (
            ema50 > ema200
            and close > ema50
            and 45 <= rsi <= 65
            and atr > 0.0005
        ):

            self.buy()