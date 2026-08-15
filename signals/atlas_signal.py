"""
Atlas AI
Signal Engine V1
"""

from research import config
from signals.features import Features


class AtlasSignal:

    @staticmethod
    def should_buy(data):

        f = Features.build(data)

        if not f["trend"]:
            return False

        if not f["price_above_ema"]:
            return False

        if not (config.RSI_MIN <= f["rsi"] <= config.RSI_MAX):
            return False

        if f["atr"] < config.ATR_MIN:
            return False

        return True

    @staticmethod
    def should_sell(data, entry_price, entry_bar):

        f = Features.build(data)

        bars = len(data.Close) - entry_bar

        if f["close"] <= entry_price - f["atr"] * config.STOP_ATR:
            return True

        if f["close"] >= entry_price + f["atr"] * config.TAKE_ATR:
            return True

        if f["ema50"] < f["ema200"]:
            return True

        if bars >= config.MAX_BARS:
            return True

        return False