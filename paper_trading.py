"""
Atlas AI
XAU/USD Paper Trading Engine

PAPER TRADING ONLY
Nessun ordine reale.
Nessun broker.
Nessun capitale reale.
"""

import json
import os
import time
import traceback

from research import config
from research.loader import ResearchLoader
from strategy.indicators import add_indicators
from signals.atlas_signal_v2 import AtlasSignalV2


# ============================================================
# CONFIGURAZIONE
# ============================================================

INITIAL_CAPITAL = 10000.0

POLL_SECONDS = 60

STATE_DIR = os.environ.get("ATLAS_STATE_DIR") or os.path.dirname(
    os.path.abspath(__file__)
)

STATE_FILE = os.path.join(STATE_DIR, "paper_state.json")

SYMBOL = "XAU/USD"


# ============================================================
# PARAMETRI BLOCCATI
# ============================================================

LOOKBACK = 20
RSI_MIN = 55

STOP_ATR = 1.2
TAKE_ATR = 1.5

ADX_MIN = 25.0


# ============================================================
# DATA WRAPPER
# ============================================================

class PaperData:

    def __init__(self, df):

        self.Close = df["Close"].to_numpy(
            dtype=float
        )

        self.High = df["High"].to_numpy(
            dtype=float
        )

        self.Low = df["Low"].to_numpy(
            dtype=float
        )

        self.EMA50 = df["EMA50"].to_numpy(
            dtype=float
        )

        self.EMA200 = df["EMA200"].to_numpy(
            dtype=float
        )

        self.RSI = df["RSI"].to_numpy(
            dtype=float
        )

        self.ATR = df["ATR"].to_numpy(
            dtype=float
        )

        self.ADX = df["ADX"].to_numpy(
            dtype=float
        )

        self.DI_PLUS = df["DI_PLUS"].to_numpy(
            dtype=float
        )

        self.DI_MINUS = df["DI_MINUS"].to_numpy(
            dtype=float
        )


# ============================================================
# STATO
# ============================================================

def default_state():

    return {
        "balance": INITIAL_CAPITAL,
        "equity": INITIAL_CAPITAL,
        "peak_equity": INITIAL_CAPITAL,
        "max_drawdown": 0.0,
        "position": None,
        "last_candle": None,
        "trades": [],
    }


def load_state():

    if not os.path.exists(STATE_FILE):

        return default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        backup = f"{STATE_FILE}.corrupt-{int(time.time())}"

        try:
            os.replace(STATE_FILE, backup)
        except Exception:
            backup = "(rinomina non riuscita)"

        print(
            "ATTENZIONE: impossibile leggere "
            f"paper_state.json. File conservato in: {backup}"
        )

        print(
            "Riparto da uno stato paper nuovo."
        )

        return default_state()


def save_state(state):

    tmp_file = f"{STATE_FILE}.tmp"

    with open(
        tmp_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=2
        )

        file.flush()
        os.fsync(file.fileno())

    os.replace(tmp_file, STATE_FILE)


# ============================================================
# CONFIGURA STRATEGIA
# ============================================================

def configure_strategy():

    AtlasSignalV2.LOOKBACK = LOOKBACK

    AtlasSignalV2.RSI_MIN = RSI_MIN

    AtlasSignalV2.ADX_MIN = ADX_MIN

    config.STOP_ATR = STOP_ATR

    config.TAKE_ATR = TAKE_ATR


# ============================================================
# CARICAMENTO MERCATO
# ============================================================

def load_market():

    loader = ResearchLoader()

    df = loader.load()

    df = df.copy()

    df = add_indicators(df)

    df = df.dropna().copy()

    return df


# ============================================================
# CONTROLLO EXIT
# ============================================================

def check_exit(
    df,
    state
):

    position = state["position"]

    if position is None:

        return None

    close = float(
        df["Close"].iloc[-1]
    )

    ema50 = float(
        df["EMA50"].iloc[-1]
    )

    ema200 = float(
        df["EMA200"].iloc[-1]
    )

    entry_price = float(
        position["entry_price"]
    )

    entry_bar = int(
        position["entry_bar"]
    )

    atr_entry = float(
        position["atr_entry"]
    )

    current_bar = len(df) - 1

    bars = current_bar - entry_bar

    # ========================================================
    # STOP LOSS FISSATO ALL'INGRESSO
    # ========================================================

    stop_price = (
        entry_price
        - atr_entry * STOP_ATR
    )

    if close <= stop_price:

        return (
            "STOP LOSS",
            close
        )

    # ========================================================
    # TAKE PROFIT FISSATO ALL'INGRESSO
    # ========================================================

    take_price = (
        entry_price
        + atr_entry * TAKE_ATR
    )

    if close >= take_price:

        return (
            "TAKE PROFIT",
            close
        )

    # ========================================================
    # TREND EXIT
    # ========================================================

    if ema50 < ema200:

        return (
            "TREND EXIT",
            close
        )

    # ========================================================
    # TIMEOUT
    # ========================================================

    if bars >= config.MAX_BARS:

        return (
            "TIMEOUT",
            close
        )

    return None


# ============================================================
# CHIUSURA POSIZIONE
# ============================================================

def close_position(
    state,
    exit_price,
    reason,
    candle_time
):

    position = state["position"]

    if position is None:

        return

    entry_price = float(
        position["entry_price"]
    )

    capital = float(
        position["capital"]
    )

    pnl_pct = (
        exit_price - entry_price
    ) / entry_price

    pnl = capital * pnl_pct

    state["balance"] += pnl

    trade = {
        "entry_time": position["entry_time"],
        "exit_time": candle_time,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl": pnl,
        "return_pct": pnl_pct * 100,
        "reason": reason,
    }

    state["trades"].append(trade)

    state["equity"] = state["balance"]

    if state["equity"] > state["peak_equity"]:

        state["peak_equity"] = state["equity"]

    drawdown = (
        state["equity"]
        - state["peak_equity"]
    ) / state["peak_equity"]

    if drawdown < state["max_drawdown"]:

        state["max_drawdown"] = drawdown

    state["position"] = None

    save_state(state)

    print()
    print("========================================")
    print("🔴 PAPER EXIT")
    print("========================================")
    print(f"Motivo       : {reason}")
    print(f"Entry        : {entry_price:.2f}")
    print(f"Exit         : {exit_price:.2f}")
    print(f"PnL          : ${pnl:.2f}")
    print(
        f"Return       : "
        f"{pnl_pct * 100:.2f}%"
    )
    print(
        f"Balance      : "
        f"${state['balance']:.2f}"
    )
    print("========================================")


# ============================================================
# APERTURA POSIZIONE
# ============================================================

def open_position(
    state,
    df,
    candle_time
):

    close = float(
        df["Close"].iloc[-1]
    )

    atr = float(
        df["ATR"].iloc[-1]
    )

    capital = float(
        state["balance"]
    )

    stop_price = (
        close
        - atr * STOP_ATR
    )

    take_price = (
        close
        + atr * TAKE_ATR
    )

    state["position"] = {
        "entry_time": candle_time,
        "entry_price": close,
        "entry_bar": len(df) - 1,
        "capital": capital,
        "atr_entry": atr,
        "stop_price": stop_price,
        "take_price": take_price,
    }

    save_state(state)

    print()
    print("========================================")
    print("🟢 PAPER BUY")
    print("========================================")
    print(f"Symbol       : {SYMBOL}")
    print(f"Entry        : {close:.2f}")
    print(f"ATR          : {atr:.2f}")
    print(
        f"Stop Loss    : "
        f"{stop_price:.2f}"
    )
    print(
        f"Take Profit  : "
        f"{take_price:.2f}"
    )
    print(
        f"Balance      : "
        f"${state['balance']:.2f}"
    )
    print("========================================")


# ============================================================
# STATUS
# ============================================================

def print_status(
    state,
    candle_time,
    close
):

    print()
    print("========================================")
    print("ATLAS AI PAPER TRADING")
    print("========================================")

    print(
        f"Ora          : {candle_time}"
    )

    print(
        f"XAU/USD      : {close:.2f}"
    )

    print(
        f"Balance      : "
        f"${state['balance']:.2f}"
    )

    print(
        f"Equity       : "
        f"${state['equity']:.2f}"
    )

    print(
        f"Trade chiusi : "
        f"{len(state['trades'])}"
    )

    print(
        f"Max Drawdown : "
        f"{state['max_drawdown'] * 100:.2f}%"
    )

    if state["position"]:

        print(
            "Posizione    : 🟢 LONG"
        )

        print(
            f"Entry        : "
            f"{state['position']['entry_price']:.2f}"
        )

    else:

        print(
            "Posizione    : ⚪ FLAT"
        )

    print("========================================")


# ============================================================
# PROCESSA MERCATO
# ============================================================

def process_market():

    df = load_market()

    if len(df) < (
        config.EMA_SLOW
        + LOOKBACK
        + 20
    ):

        raise RuntimeError(
            "Dati insufficienti "
            "per la strategia."
        )

    # ========================================================
    # USA SOLO L'ULTIMA CANDELA H1 COMPLETAMENTE CHIUSA
    # ========================================================

    closed_df = df.iloc[:-1].copy()

    if len(closed_df) < (
        config.EMA_SLOW
        + LOOKBACK
        + 20
    ):

        raise RuntimeError(
            "Dati insufficienti "
            "per la candela chiusa."
        )

    candle_time = str(
        closed_df.index[-1]
    )

    close = float(
        closed_df["Close"].iloc[-1]
    )

    state = load_state()

    # ========================================================
    # NESSUNA NUOVA CANDELA
    # ========================================================

    if (
        state["last_candle"]
        == candle_time
    ):

        return

    # ========================================================
    # NUOVA CANDELA CHIUSA
    # ========================================================

    print()
    print(
        f"NUOVA CANDELA CHIUSA: {candle_time}"
    )

    print(
        f"XAU/USD: {close:.2f}"
    )

    # ========================================================
    # EXIT
    # ========================================================

    if state["position"]:

        exit_signal = check_exit(
            closed_df,
            state
        )

        if exit_signal:

            reason, exit_price = (
                exit_signal
            )

            close_position(
                state,
                exit_price,
                reason,
                candle_time
            )

    # ========================================================
    # ENTRY
    # ========================================================

    if state["position"] is None:

        data = PaperData(
            closed_df
        )

        buy_signal = (
            AtlasSignalV2.should_buy(
                data
            )
        )

        if buy_signal:

            open_position(
                state,
                closed_df,
                candle_time
            )

        else:

            print(
                "Segnale: NO TRADE"
            )

    # ========================================================
    # SALVATAGGIO
    # ========================================================

    state["last_candle"] = candle_time

    state["equity"] = state["balance"]

    save_state(state)

    print_status(
        state,
        candle_time,
        close
    )


# ============================================================
# MAIN
# ============================================================

def main():

    configure_strategy()

    print()
    print("========================================")
    print("ATLAS AI")
    print("XAU/USD PAPER TRADING")
    print("========================================")

    print()
    print(
        "CAPITALE VIRTUALE : $10,000"
    )

    print(
        "ORDINI REALI      : NO"
    )

    print(
        "BROKER             : NO"
    )

    print()
    print("PARAMETRI BLOCCATI")
    print()
    print("EMA       : 50 / 200")
    print("Lookback  : 20")
    print("RSI       : 55")
    print("SL        : 1.2 ATR")
    print("TP        : 1.5 ATR")
    print("ADX       : >= 25")
    print("DI+       : > DI-")

    print()
    print("========================================")
    print()
    print(
        "Atlas è in attesa di una nuova candela..."
    )

    while True:

        try:

            process_market()

        except KeyboardInterrupt:

            print()
            print(
                "Paper trading arrestato."
            )

            break

        except Exception as error:

            print()
            print("========================================")
            print("DATI NON DISPONIBILI")
            print("========================================")
            print(
                "La fonte dati non ha restituito "
                "dati validi."
            )
            print(
                "Atlas NON modifica lo stato "
                "e ritenterà automaticamente."
            )
            print(
                f"Dettaglio: {error}"
            )
            print("========================================")

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    main()