"""
Atlas AI
Strategy V2
"""


class AtlasSignalV2:

    @staticmethod
    def should_buy(data):

        if len(data.Close) < 201:
            return False

        close = float(data.Close[-1])

        previous_close = float(data.Close[-2])

        ema50 = float(data.EMA50[-1])

        ema200 = float(data.EMA200[-1])

        rsi = float(data.RSI[-1])

        atr = float(data.ATR[-1])

        # Trend principale
        trend = ema50 > ema200

        # Pullback vicino alla EMA50
        pullback = abs(close - ema50) <= atr

        # RSI neutro
        rsi_ok = 45 <= rsi <= 55

        # Candela di conferma
        confirmation = close > previous_close

        return (
            trend
            and pullback
            and rsi_ok
            and confirmation
        )