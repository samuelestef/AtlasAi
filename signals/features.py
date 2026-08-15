"""
Atlas AI
Feature Engine
"""


class Features:

    @staticmethod
    def build(data):

        close = float(data.Close[-1])

        previous_close = float(data.Close[-2])

        high = float(data.High[-1])

        low = float(data.Low[-1])

        ema50 = float(data.EMA50[-1])

        ema200 = float(data.EMA200[-1])

        rsi = float(data.RSI[-1])

        atr = float(data.ATR[-1])

        return {

            "trend": ema50 > ema200,

            "price_above_ema": close > ema50,

            "rsi": rsi,

            "atr": atr,

            "bullish": close > previous_close,

            "distance_ema": close - ema50,

            "candle_range": high - low,

            "close": close,

            "ema50": ema50,

            "ema200": ema200

        }