
"""
Atlas AI
XAU/USD Active M15 Paper Trading Engine

PAPER TRADING ONLY
Nessun ordine reale.
Nessun broker.
Nessun capitale reale.

Motore separato dal Core H1.
"""

import json
import os
import time
import traceback

import requests
import yfinance as yf
import ta

from dotenv import load_dotenv


# ============================================================
# CONFIGURAZIONE
# ============================================================

SYMBOL = "GC=F"
DISPLAY_SYMBOL = "XAU/USD"

INTERVAL = "15m"

INITIAL_CAPITAL = 10000.0

POLL_SECONDS = 60

STATE_DIR = os.environ.get("ATLAS_STATE_DIR") or os.path.dirname(
    os.path.abspath(__file__)
)

STATE_FILE = os.path.join(STATE_DIR, "active_m15_state.json")


# ============================================================
# PARAMETRI ACTIVE M15
# ============================================================

EMA_FAST = 20
EMA_SLOW = 50

RSI_PERIOD = 14

RSI_LONG = 55.0
RSI_SHORT = 45.0

ADX_PERIOD = 14
ADX_MIN = 20.0

ATR_PERIOD = 14

STOP_ATR = 1.0
TAKE_ATR = 1.5

MAX_BARS = 16


# ============================================================
# TELEGRAM
# ============================================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
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

    if not os.path.exists(
        STATE_FILE
    ):

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
            f"active_m15_state.json. File conservato in: {backup}"
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
# TELEGRAM
# ============================================================

def telegram_send(message):

    if not TELEGRAM_TOKEN:

        print(
            "⚠️ TELEGRAM_BOT_TOKEN non configurato."
        )

        return False

    if not TELEGRAM_CHAT_ID:

        print(
            "⚠️ TELEGRAM_CHAT_ID non configurato."
        )

        return False

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:

        response = requests.post(
            url,
            data=payload,
            timeout=20,
        )

        if response.status_code == 200:

            result = response.json()

            if result.get("ok"):

                print(
                    "📨 Telegram Active: messaggio inviato."
                )

                return True

        print(
            "⚠️ Telegram HTTP "
            f"{response.status_code}: "
            f"{response.text}"
        )

    except Exception as error:

        print(
            f"⚠️ Errore Telegram: {error}"
        )

    return False


# ============================================================
# MARKET DATA
# ============================================================

def load_market():

    last_error = None

    for attempt in range(3):

        try:

            df = yf.download(
                SYMBOL,
                period="60d",
                interval=INTERVAL,
                auto_adjust=False,
                progress=False,
            )

            if df.empty:

                raise RuntimeError(
                    "Yahoo Finance ha restituito "
                    "un DataFrame vuoto."
                )

            if hasattr(
                df.columns,
                "levels"
            ):

                if len(
                    df.columns.levels
                ) > 1:

                    df.columns = (
                        df.columns
                        .get_level_values(0)
                    )

            required = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]

            missing = [
                column
                for column in required
                if column not in df.columns
            ]

            if missing:

                raise RuntimeError(
                    f"Colonne mancanti: {missing}"
                )

            df = df[required].copy()

            df = df.dropna()

            df = df.sort_index()

            df = df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]

            # ========================================================
            # INDICATORI
            # ========================================================

            df["EMA20"] = ta.trend.ema_indicator(
                close=df["Close"],
                window=EMA_FAST
            )

            df["EMA50"] = ta.trend.ema_indicator(
                close=df["Close"],
                window=EMA_SLOW
            )

            df["RSI"] = ta.momentum.rsi(
                close=df["Close"],
                window=RSI_PERIOD
            )

            df["ATR"] = (
                ta.volatility.average_true_range(
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    window=ATR_PERIOD
                )
            )

            df["ADX"] = ta.trend.adx(
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                window=ADX_PERIOD
            )

            df["DI_PLUS"] = ta.trend.adx_pos(
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                window=ADX_PERIOD
            )

            df["DI_MINUS"] = ta.trend.adx_neg(
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                window=ADX_PERIOD
            )

            df = df.dropna()

            if len(df) < 100:

                raise RuntimeError(
                    "Dati M15 insufficienti "
                    "per la strategia."
                )

            return df

        except Exception as error:

            last_error = error

            if attempt < 2:

                wait_seconds = 5 * (attempt + 1)

                print(
                    "⚠️ Yahoo Finance: "
                    f"tentativo {attempt + 1}/3 fallito."
                )

                print(
                    f"   Motivo: {error}"
                )

                print(
                    f"   Nuovo tentativo tra "
                    f"{wait_seconds} secondi..."
                )

                time.sleep(
                    wait_seconds
                )

    raise RuntimeError(
        "Impossibile ottenere dati M15 "
        "da Yahoo Finance dopo 3 tentativi. "
        f"Ultimo errore: {last_error}"
    )


# ============================================================
# SEGNALI
# ============================================================

def check_signal(df):

    # --------------------------------------------------------
    # USIAMO SOLO LA CANDELA M15 CHIUSA
    # --------------------------------------------------------

    current = df.iloc[-2]
    previous = df.iloc[-3]

    close = float(
        current["Close"]
    )

    previous_close = float(
        previous["Close"]
    )

    ema20 = float(
        current["EMA20"]
    )

    ema50 = float(
        current["EMA50"]
    )

    rsi = float(
        current["RSI"]
    )

    adx = float(
        current["ADX"]
    )

    di_plus = float(
        current["DI_PLUS"]
    )

    di_minus = float(
        current["DI_MINUS"]
    )

    bullish_candle = (
        close > previous_close
    )

    bearish_candle = (
        close < previous_close
    )

    # ========================================================
    # LONG
    # ========================================================

    long_signal = (
        ema20 > ema50
        and close > ema20
        and rsi >= RSI_LONG
        and adx >= ADX_MIN
        and di_plus > di_minus
        and bullish_candle
    )

    if long_signal:

        return "LONG"

    # ========================================================
    # SHORT
    # ========================================================

    short_signal = (
        ema20 < ema50
        and close < ema20
        and rsi <= RSI_SHORT
        and adx >= ADX_MIN
        and di_minus > di_plus
        and bearish_candle
    )

    if short_signal:

        return "SHORT"

    return None


# ============================================================
# POSITION EXIT
# ============================================================

def check_exit(
    df,
    position
):

    current = df.iloc[-2]

    close = float(
        current["Close"]
    )

    ema20 = float(
        current["EMA20"]
    )

    ema50 = float(
        current["EMA50"]
    )

    entry_price = float(
        position["entry_price"]
    )

    stop_price = float(
        position["stop_price"]
    )

    take_price = float(
        position["take_price"]
    )

    entry_bar = int(
        position["entry_bar"]
    )

    current_bar = (
        len(df) - 2
    )

    bars = (
        current_bar
        - entry_bar
    )

    direction = position[
        "direction"
    ]

    # ========================================================
    # LONG
    # ========================================================

    if direction == "LONG":

        if close <= stop_price:

            return (
                "STOP LOSS",
                close
            )

        if close >= take_price:

            return (
                "TAKE PROFIT",
                close
            )

        if ema20 < ema50:

            return (
                "TREND EXIT",
                close
            )

    # ========================================================
    # SHORT
    # ========================================================

    if direction == "SHORT":

        if close >= stop_price:

            return (
                "STOP LOSS",
                close
            )

        if close <= take_price:

            return (
                "TAKE PROFIT",
                close
            )

        if ema20 > ema50:

            return (
                "TREND EXIT",
                close
            )

    # ========================================================
    # TIMEOUT
    # ========================================================

    if bars >= MAX_BARS:

        return (
            "TIMEOUT",
            close
        )

    return None


# ============================================================
# OPEN POSITION
# ============================================================

def open_position(
    state,
    df,
    direction,
    candle_time
):

    current = df.iloc[-2]

    close = float(
        current["Close"]
    )

    atr = float(
        current["ATR"]
    )

    capital = float(
        state["balance"]
    )

    if direction == "LONG":

        stop_price = (
            close
            - atr * STOP_ATR
        )

        take_price = (
            close
            + atr * TAKE_ATR
        )

    else:

        stop_price = (
            close
            + atr * STOP_ATR
        )

        take_price = (
            close
            - atr * TAKE_ATR
        )

    position = {
        "direction": direction,
        "entry_time": candle_time,
        "entry_price": close,
        "entry_bar": len(df) - 2,
        "capital": capital,
        "atr_entry": atr,
        "stop_price": stop_price,
        "take_price": take_price,
    }

    state["position"] = position

    save_state(state)

    print()
    print("========================================")
    print("🟣 ATLAS ACTIVE M15")
    print("========================================")
    print(
        f"Direction    : {direction}"
    )
    print(
        f"Entry        : {close:.2f}"
    )
    print(
        f"ATR          : {atr:.2f}"
    )
    print(
        f"Stop Loss    : {stop_price:.2f}"
    )
    print(
        f"Take Profit  : {take_price:.2f}"
    )
    print(
        f"Candle       : {candle_time}"
    )
    print("Paper Trade  : YES")
    print("Real Orders  : NO")
    print("========================================")

    send_entry_telegram(
        position
    )


# ============================================================
# CLOSE POSITION
# ============================================================

def close_position(
    state,
    exit_price,
    reason,
    candle_time
):

    position = state[
        "position"
    ]

    if position is None:

        return

    entry_price = float(
        position["entry_price"]
    )

    capital = float(
        position["capital"]
    )

    direction = position[
        "direction"
    ]

    if direction == "LONG":

        pnl_pct = (
            exit_price
            - entry_price
        ) / entry_price

    else:

        pnl_pct = (
            entry_price
            - exit_price
        ) / entry_price

    pnl = (
        capital
        * pnl_pct
    )

    state["balance"] = (
        state["balance"]
        + pnl
    )

    state["equity"] = (
        state["balance"]
    )

    if state["equity"] > state[
        "peak_equity"
    ]:

        state["peak_equity"] = (
            state["equity"]
        )

    drawdown = (
        state["equity"]
        - state["peak_equity"]
    ) / state["peak_equity"]

    if drawdown < state[
        "max_drawdown"
    ]:

        state["max_drawdown"] = (
            drawdown
        )

    trade = {
        "direction": direction,
        "entry_time": position[
            "entry_time"
        ],
        "entry_price": entry_price,
        "exit_time": candle_time,
        "exit_price": exit_price,
        "atr_entry": position[
            "atr_entry"
        ],
        "stop_price": position[
            "stop_price"
        ],
        "take_price": position[
            "take_price"
        ],
        "pnl": pnl,
        "return_pct": pnl_pct * 100,
        "reason": reason,
    }

    state["trades"].append(
        trade
    )

    state["position"] = None

    save_state(state)

    print()
    print("========================================")
    print("🟣 ATLAS ACTIVE M15 CLOSED")
    print("========================================")
    print(
        f"Direction    : {direction}"
    )
    print(
        f"Entry        : {entry_price:.2f}"
    )
    print(
        f"Exit         : {exit_price:.2f}"
    )
    print(
        f"PnL          : ${pnl:+.2f}"
    )
    print(
        f"Return       : {pnl_pct * 100:+.2f}%"
    )
    print(
        f"Reason       : {reason}"
    )
    print("========================================")

    send_exit_telegram(
        trade
    )


# ============================================================
# TELEGRAM ENTRY
# ============================================================

def send_entry_telegram(
    position
):

    direction = position[
        "direction"
    ]

    emoji = (
        "🟢"
        if direction == "LONG"
        else "🔴"
    )

    message = f"""
🟣 ATLAS AI ACTIVE M15

XAU/USD

{emoji} {direction}

━━━━━━━━━━━━━━━━━━━━

🎯 ENTRY
{position["entry_price"]:.2f}

🛑 STOP LOSS
{position["stop_price"]:.2f}

💰 TAKE PROFIT
{position["take_price"]:.2f}

📊 ATR
{position["atr_entry"]:.2f}

🕐 CANDLE
{position["entry_time"]}

━━━━━━━━━━━━━━━━━━━━

🟣 PAPER TRADE
🔴 ORDINI REALI: NO

⚠️ Segnale generato
da Atlas AI Active M15.
"""

    telegram_send(
        message
    )


# ============================================================
# TELEGRAM EXIT
# ============================================================

def send_exit_telegram(
    trade
):

    pnl = float(
        trade["pnl"]
    )

    if pnl > 0:

        result = "🟢 PROFITTO"

    elif pnl < 0:

        result = "🔴 PERDITA"

    else:

        result = "⚪ BREAK EVEN"

    message = f"""
🔔 ATLAS AI ACTIVE M15 CLOSED

XAU/USD

{result}

━━━━━━━━━━━━━━━━━━━━

{trade["direction"]}

ENTRY
{trade["entry_price"]:.2f}

EXIT
{trade["exit_price"]:.2f}

━━━━━━━━━━━━━━━━━━━━

💰 PnL
${pnl:+.2f}

📊 Return
{trade["return_pct"]:+.2f}%

📌 Motivo
{trade["reason"]}

━━━━━━━━━━━━━━━━━━━━

🟣 PAPER TRADE
🔴 ORDINI REALI: NO
"""

    telegram_send(
        message
    )


# ============================================================
# STATUS
# ============================================================

def print_status(
    state,
    candle_time,
    close
):

    position = state[
        "position"
    ]

    if position:

        position_text = (
            f'{position["direction"]} '
            f'@ {position["entry_price"]:.2f}'
        )

    else:

        position_text = "⚪ FLAT"

    print()
    print("========================================")
    print("ATLAS AI ACTIVE M15")
    print("========================================")
    print(
        f"Candle       : {candle_time}"
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
    print(
        f"Posizione    : "
        f"{position_text}"
    )
    print("========================================")


# ============================================================
# PROCESS MARKET
# ============================================================

def process_market():

    df = load_market()

    # --------------------------------------------------------
    # ULTIMA CANDELA COMPLETAMENTE CHIUSA
    # --------------------------------------------------------

    closed = df.iloc[-2]

    candle_time = str(
        df.index[-2]
    )

    close = float(
        closed["Close"]
    )

    state = load_state()

    # ========================================================
    # NESSUNA NUOVA CANDELA
    # ========================================================

    if state["last_candle"] == candle_time:

        return

    print()
    print(
        f"NUOVA CANDELA M15 CHIUSA: "
        f"{candle_time}"
    )

    print(
        f"XAU/USD: {close:.2f}"
    )

    # ========================================================
    # EXIT
    # ========================================================

    if state["position"]:

        exit_signal = check_exit(
            df,
            state["position"]
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

        signal = check_signal(
            df
        )

        if signal:

            open_position(
                state,
                df,
                signal,
                candle_time
            )

        else:

            print(
                "Segnale: NO TRADE"
            )

    # ========================================================
    # SALVATAGGIO
    # ========================================================

    state["last_candle"] = (
        candle_time
    )

    state["equity"] = (
        state["balance"]
    )

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

    print()
    print("========================================")
    print("ATLAS AI ACTIVE M15")
    print("========================================")
    print(
        "CAPITALE VIRTUALE : $10,000"
    )
    print(
        "ORDINI REALI      : NO"
    )
    print(
        "BROKER            : NO"
    )
    print()
    print(
        "TIMEFRAME         : M15"
    )
    print(
        "EMA               : 20 / 50"
    )
    print(
        "RSI LONG          : >= 55"
    )
    print(
        "RSI SHORT         : <= 45"
    )
    print(
        "ADX               : >= 20"
    )
    print(
        "SL                : 1.0 ATR"
    )
    print(
        "TP                : 1.5 ATR"
    )
    print(
        "TIMEOUT           : 16 M15"
    )
    print()
    print(
        "Atlas Active è in attesa "
        "di una nuova candela M15..."
    )
    print()

    while True:

        try:

            process_market()

        except KeyboardInterrupt:

            print()
            print(
                "Atlas Active M15 arrestato."
            )

            break

        except Exception:

            print()
            print(
                "ERRORE ACTIVE M15:"
            )

            traceback.print_exc()

        time.sleep(
            POLL_SECONDS
        )


if __name__ == "__main__":

    main()

