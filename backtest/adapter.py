"""
Atlas AI
Backtesting Adapter
"""

from backtesting import Strategy

from research import config
from signals.atlas_signal_v2 import AtlasSignalV2


class AtlasBacktestStrategy(Strategy):

    DEBUG = False

    def init(self):

        self.entry_bar = None
        self.entry_price = None

    def next(self):

        if len(self.data.Close) < (
            config.EMA_SLOW
            + AtlasSignalV2.LOOKBACK
            + 10
        ):
            return

        close = float(
            self.data.Close[-1]
        )

        atr = float(
            self.data.ATR[-1]
        )

        # ==================================
        # GESTIONE POSIZIONE
        # ==================================

        if self.position:

            bars = (
                len(self.data.Close)
                - self.entry_bar
            )

            # STOP LOSS
            if close <= (
                self.entry_price
                - atr * config.STOP_ATR
            ):

                self.position.close()
                return

            # TAKE PROFIT
            if close >= (
                self.entry_price
                + atr * config.TAKE_ATR
            ):

                self.position.close()
                return

            # TREND EXIT
            ema50 = float(
                self.data.EMA50[-1]
            )

            ema200 = float(
                self.data.EMA200[-1]
            )

            if ema50 < ema200:

                self.position.close()
                return

            # TIMEOUT
            if bars >= config.MAX_BARS:

                self.position.close()
                return

            return

        # ==================================
        # NUOVO SEGNALE
        # ==================================

        if AtlasSignalV2.should_buy(
            self.data
        ):

            self.entry_bar = (
                len(self.data.Close)
            )

            self.entry_price = close

            self.buy()