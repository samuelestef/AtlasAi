"""
Atlas AI
Momentum Strategy
Dynamic Trend Regime
"""

from research import config


class AtlasSignalV2:

    LOOKBACK = 20
    RSI_MIN = 55

    ADX_MIN = 25.0

    @staticmethod
    def should_buy(data):

        minimum_bars = (
            config.EMA_SLOW
            + AtlasSignalV2.LOOKBACK
            + 10
        )

        if len(data.Close) < minimum_bars:
            return False

        close = float(data.Close[-1])

        ema50 = float(data.EMA50[-1])
        ema200 = float(data.EMA200[-1])

        rsi = float(data.RSI[-1])

        adx = float(data.ADX[-1])
        di_plus = float(data.DI_PLUS[-1])
        di_minus = float(data.DI_MINUS[-1])

        previous_close = float(
            data.Close[-2]
        )

        # ==================================
        # TREND DIRECTION
        # ==================================

        trend = ema50 > ema200

        above_ema = close > ema50

        # ==================================
        # MOMENTUM
        # ==================================

        momentum = (
            rsi >= AtlasSignalV2.RSI_MIN
        )

        bullish_candle = (
            close > previous_close
        )

        # ==================================
        # BREAKOUT
        # ==================================

        recent_highs = [
            float(data.High[-i])
            for i in range(
                2,
                AtlasSignalV2.LOOKBACK + 2
            )
        ]

        recent_high = max(
            recent_highs
        )

        breakout = (
            close > recent_high
        )

        # ==================================
        # DYNAMIC REGIME
        # ==================================

        trending_market = (
            adx >= AtlasSignalV2.ADX_MIN
        )

        bullish_regime = (
            di_plus > di_minus
        )

        # ==================================
        # FINAL SIGNAL
        # ==================================

        return (
            trend
            and above_ema
            and momentum
            and bullish_candle
            and breakout
            and trending_market
            and bullish_regime
        )

    @staticmethod
    def should_sell(
        data,
        entry_price,
        entry_bar
    ):

        close = float(
            data.Close[-1]
        )

        ema50 = float(
            data.EMA50[-1]
        )

        ema200 = float(
            data.EMA200[-1]
        )

        atr = float(
            data.ATR[-1]
        )

        bars = (
            len(data.Close)
            - entry_bar
        )

        # STOP LOSS
        if close <= (
            entry_price
            - atr * config.STOP_ATR
        ):
            return True

        # TAKE PROFIT
        if close >= (
            entry_price
            + atr * config.TAKE_ATR
        ):
            return True

        # TREND EXIT
        if ema50 < ema200:
            return True

        # TIMEOUT
        if bars >= config.MAX_BARS:
            return True

        return False