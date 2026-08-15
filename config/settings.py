"""
Atlas AI
Global Strategy Settings
"""


class Settings:

    # ==========================
    # Indicatori
    # ==========================

    EMA_FAST = 50
    EMA_SLOW = 200

    RSI_MIN = 45
    RSI_MAX = 65

    ATR_MIN = 0.0005

    # ==========================
    # Gestione posizione
    # ==========================

    STOP_ATR = 2.0

    TAKE_ATR = 3.0

    MAX_BARS_IN_TRADE = 40

    # ==========================
    # Backtest
    # ==========================

    INITIAL_CASH = 10000

    COMMISSION = 0.0002