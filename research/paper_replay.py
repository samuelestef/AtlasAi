"""
ATLAS AI
XAU/USD PAPER REPLAY V3

Replica il comportamento del backtest/adapter.py.

IMPORTANTE:
- PAPER ONLY
- nessun ordine reale
- entrata sulla candela successiva al segnale
- stessa strategia AtlasSignalV2
- stessi parametri bloccati
"""

from research import config
from research.loader import ResearchLoader
from strategy.indicators import add_indicators
from signals.atlas_signal_v2 import AtlasSignalV2


# ============================================================
# PARAMETRI BLOCCATI
# ============================================================

INITIAL_CAPITAL = 10000.0

LOOKBACK = 20
RSI_MIN = 55
ADX_MIN = 25.0

STOP_ATR = 1.2
TAKE_ATR = 1.5


# ============================================================
# DATA WRAPPER
# ============================================================

class ReplayData:

    def __init__(self, df):

        self.Close = df["Close"].to_numpy(dtype=float)
        self.High = df["High"].to_numpy(dtype=float)
        self.Low = df["Low"].to_numpy(dtype=float)

        self.EMA50 = df["EMA50"].to_numpy(dtype=float)
        self.EMA200 = df["EMA200"].to_numpy(dtype=float)

        self.RSI = df["RSI"].to_numpy(dtype=float)
        self.ATR = df["ATR"].to_numpy(dtype=float)

        self.ADX = df["ADX"].to_numpy(dtype=float)
        self.DI_PLUS = df["DI_PLUS"].to_numpy(dtype=float)
        self.DI_MINUS = df["DI_MINUS"].to_numpy(dtype=float)


# ============================================================
# DATA
# ============================================================

def load_data():

    df = ResearchLoader().load()

    df = add_indicators(df)

    df = df.dropna().copy()

    return df


# ============================================================
# EXIT
#
# IDENTICA ALL'ADAPTER
# ============================================================

def check_exit(
    data,
    entry_price,
    entry_bar,
):

    close = float(
        data.Close[-1]
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

        return True, "STOP LOSS"

    # TAKE PROFIT
    if close >= (
        entry_price
        + atr * config.TAKE_ATR
    ):

        return True, "TAKE PROFIT"

    # TREND EXIT
    ema50 = float(
        data.EMA50[-1]
    )

    ema200 = float(
        data.EMA200[-1]
    )

    if ema50 < ema200:

        return True, "TREND EXIT"

    # TIMEOUT
    if bars >= config.MAX_BARS:

        return True, "TIMEOUT"

    return False, None


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD PAPER REPLAY V3")
    print("========================================")

    print()
    print("PARAMETRI BLOCCATI")
    print("----------------------------------------")

    print("EMA       : 50 / 200")
    print("Lookback  : 20")
    print("RSI       : 55")
    print("SL        : 1.2 ATR")
    print("TP        : 1.5 ATR")
    print("ADX       : >= 25")
    print("DI+       : > DI-")

    # ========================================================
    # CONFIGURAZIONE
    # ========================================================

    AtlasSignalV2.LOOKBACK = LOOKBACK
    AtlasSignalV2.RSI_MIN = RSI_MIN
    AtlasSignalV2.ADX_MIN = ADX_MIN

    config.STOP_ATR = STOP_ATR
    config.TAKE_ATR = TAKE_ATR

    # ========================================================
    # DATA
    # ========================================================

    print()
    print("Caricamento dati...")

    df = load_data()

    print(
        f"Candele disponibili : {len(df)}"
    )

    # ========================================================
    # CAPITALE
    # ========================================================

    balance = INITIAL_CAPITAL

    peak_equity = INITIAL_CAPITAL

    max_drawdown = 0.0

    position = None

    pending_entry = False
    pending_signal_bar = None

    trades = []

    # ========================================================
    # BARRA INIZIALE
    # ========================================================

    start_bar = (
        config.EMA_SLOW
        + AtlasSignalV2.LOOKBACK
        + 10
    )

    print(
        f"Barra iniziale      : {start_bar}"
    )

    print()
    print("========================================")
    print("REPLAY V3 IN CORSO")
    print("========================================")

    # ========================================================
    # LOOP
    # ========================================================

    for bar in range(
        start_bar,
        len(df)
    ):

        # ----------------------------------------------------
        # DATA DISPONIBILE FINO ALLA CANDELA CORRENTE
        # ----------------------------------------------------

        window = df.iloc[
            :bar + 1
        ].copy()

        data = ReplayData(
            window
        )

        candle_time = str(
            df.index[bar]
        )

        open_price = float(
            df["Open"].iloc[bar]
        )

        close = float(
            df["Close"].iloc[bar]
        )

        # ====================================================
        # ESECUZIONE ORDINE PENDENTE
        #
        # Il segnale viene generato sulla candela precedente.
        # L'ordine viene eseguito sull'OPEN della candela corrente.
        # ====================================================

        if (
            pending_entry
            and position is None
        ):

            entry_price = open_price

            position = {

                "entry_time":
                    candle_time,

                "signal_bar":
                    pending_signal_bar,

                "entry_bar":
                    len(data.Close),

                "entry_price":
                    entry_price,

                "capital":
                    balance,
            }

            pending_entry = False

            atr = float(
                data.ATR[-1]
            )

            print()
            print(
                f"[{candle_time}]"
            )

            print(
                "🟢 ENTRY"
            )

            print(
                f"Price : "
                f"{entry_price:.2f}"
            )

            print(
                f"ATR   : "
                f"{atr:.2f}"
            )

            print(
                f"SL    : "
                f"{entry_price - atr * STOP_ATR:.2f}"
            )

            print(
                f"TP    : "
                f"{entry_price + atr * TAKE_ATR:.2f}"
            )

        # ====================================================
        # GESTIONE POSIZIONE
        # ====================================================

        if position is not None:

            should_exit, reason = check_exit(
                data,
                position["entry_price"],
                position["entry_bar"],
            )

            if should_exit:

                entry_price = float(
                    position["entry_price"]
                )

                capital = float(
                    position["capital"]
                )

                pnl_pct = (
                    close
                    - entry_price
                ) / entry_price

                pnl = (
                    capital
                    * pnl_pct
                )

                balance += pnl

                trades.append(
                    {
                        "entry_time":
                            position["entry_time"],

                        "exit_time":
                            candle_time,

                        "entry_price":
                            entry_price,

                        "exit_price":
                            close,

                        "pnl":
                            pnl,

                        "return_pct":
                            pnl_pct * 100,

                        "reason":
                            reason,
                    }
                )

                if balance > peak_equity:

                    peak_equity = balance

                drawdown = (
                    balance
                    - peak_equity
                ) / peak_equity

                if drawdown < max_drawdown:

                    max_drawdown = drawdown

                print()
                print(
                    f"[{candle_time}]"
                )

                print(
                    f"🔴 EXIT | {reason}"
                )

                print(
                    f"Entry : "
                    f"{entry_price:.2f}"
                )

                print(
                    f"Exit  : "
                    f"{close:.2f}"
                )

                print(
                    f"PnL   : "
                    f"${pnl:.2f}"
                )

                position = None

                # ============================================
                # IMPORTANTISSIMO
                #
                # Dopo una chiusura non cerchiamo un nuovo
                # segnale sulla stessa candela.
                # ============================================

                continue

            # ------------------------------------------------
            # POSIZIONE APERTA
            # ------------------------------------------------

            continue

        # ====================================================
        # NUOVO SEGNALE
        #
        # Il segnale viene registrato ora.
        # L'entrata avverrà sulla prossima candela.
        # ====================================================

        if AtlasSignalV2.should_buy(
            data
        ):

            pending_entry = True

            pending_signal_bar = bar

            print()
            print(
                f"[{candle_time}]"
            )

            print(
                "📡 SIGNAL"
            )

            print(
                "BUY previsto sulla "
                "prossima candela"
            )

    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("========================================")
    print("ATLAS AI XAU/USD PAPER REPLAY V3")
    print("REPORT")
    print("========================================")

    total_trades = len(
        trades
    )

    if total_trades == 0:

        print()
        print(
            "Trades           : 0"
        )

        print(
            "Nessun trade."
        )

        print(
            "========================================"
        )

        return

    wins = [
        trade
        for trade in trades
        if trade["pnl"] > 0
    ]

    losses = [
        trade
        for trade in trades
        if trade["pnl"] < 0
    ]

    win_rate = (
        len(wins)
        / total_trades
        * 100
    )

    gross_profit = sum(
        trade["pnl"]
        for trade in wins
    )

    gross_loss = abs(
        sum(
            trade["pnl"]
            for trade in losses
        )
    )

    if gross_loss > 0:

        profit_factor = (
            gross_profit
            / gross_loss
        )

    else:

        profit_factor = float(
            "inf"
        )

    total_return = (
        balance
        - INITIAL_CAPITAL
    ) / INITIAL_CAPITAL * 100

    print()
    print(
        f"Trades           : "
        f"{total_trades}"
    )

    print(
        f"Win Rate         : "
        f"{win_rate:.2f}%"
    )

    print(
        f"Return           : "
        f"{total_return:.2f}%"
    )

    print(
        f"Profit Factor    : "
        f"{profit_factor:.3f}"
    )

    print(
        f"Drawdown         : "
        f"{max_drawdown * 100:.2f}%"
    )

    print(
        f"Equity Finale    : "
        f"${balance:.2f}"
    )

    if position is not None:

        print()
        print(
            "⚠️ Posizione aperta "
            "alla fine del replay."
        )

        print(
            f"Entry : "
            f"{position['entry_price']:.2f}"
        )

    print()
    print("========================================")


if __name__ == "__main__":

    main()