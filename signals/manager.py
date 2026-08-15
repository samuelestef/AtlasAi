"""
Atlas AI
Signal Manager
"""

from signals.atlas_signal_v2 import AtlasSignalV2


class SignalManager:

    @staticmethod
    def should_buy(data):

        return AtlasSignalV2.should_buy(data)

    @staticmethod
    def should_sell(
        data,
        entry_price,
        entry_bar
    ):

        return AtlasSignalV2.should_sell(
            data,
            entry_price,
            entry_bar
        )