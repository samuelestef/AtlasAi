import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# ATLAS AI
# TELEGRAM ALERT MONITOR
# ============================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_DIR = Path(__file__).resolve().parent

STATE_FILE = BASE_DIR / "paper_state.json"
ALERT_STATE_FILE = BASE_DIR / "telegram_alert_state.json"

POLL_SECONDS = 5

INITIAL_CAPITAL = 10000.0


# ============================================================
# VALIDAZIONE
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN non trovato nel file .env"
    )

if not CHAT_ID:
    raise RuntimeError(
        "TELEGRAM_CHAT_ID non trovato nel file .env"
    )


# ============================================================
# DEFAULT
# ============================================================

def default_alert_state():

    return {
        "last_trade_count": 0,
        "last_position_id": None,
    }


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path, default):

    if not path.exists():
        return default

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"⚠️ Errore lettura {path.name}: {error}"
        )

        return default


# ============================================================
# SAVE JSON
# ============================================================

def save_json(path, data):

    try:

        temp_path = path.with_suffix(
            ".tmp"
        )

        with open(
            temp_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temp_path.replace(path)

    except Exception as error:

        print(
            f"⚠️ Errore salvataggio {path.name}: {error}"
        )


# ============================================================
# LOAD PAPER STATE
# ============================================================

def load_paper_state():

    return load_json(
        STATE_FILE,
        {
            "balance": INITIAL_CAPITAL,
            "equity": INITIAL_CAPITAL,
            "trades": [],
            "position": None,
        },
    )


# ============================================================
# LOAD ALERT STATE
# ============================================================

def load_alert_state():

    return load_json(
        ALERT_STATE_FILE,
        default_alert_state(),
    )


# ============================================================
# TELEGRAM API
# ============================================================

def telegram_send(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    attempts = 5

    for attempt in range(
        1,
        attempts + 1,
    ):

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
                        "📨 Telegram: messaggio inviato."
                    )

                    return True

            print(
                f"⚠️ Telegram HTTP "
                f"{response.status_code}: "
                f"{response.text}"
            )

        except Exception as error:

            print(
                f"⚠️ Errore Telegram "
                f"(tentativo {attempt}/{attempts}): "
                f"{error}"
            )

        if attempt < attempts:

            time.sleep(
                min(
                    5 * attempt,
                    20,
                )
            )

    print(
        "❌ Invio Telegram fallito."
    )

    return False


# ============================================================
# POSITION ID
# ============================================================

def get_position_id(position):

    if not position:
        return None

    entry_time = position.get(
        "entry_time",
        "",
    )

    entry_price = position.get(
        "entry_price",
        "",
    )

    return (
        f"{entry_time}|"
        f"{entry_price}"
    )


# ============================================================
# ENTRY MESSAGE
# ============================================================

def format_entry(position):

    entry = float(
        position.get(
            "entry_price",
            0,
        )
    )

    atr = float(
        position.get(
            "atr_entry",
            0,
        )
    )

    stop = (
        entry
        - atr * 1.2
    )

    target = (
        entry
        + atr * 1.5
    )

    entry_time = position.get(
        "entry_time",
        "N/D",
    )

    return f"""
🚨 ATLAS AI SIGNAL

XAU/USD

🟢 LONG

━━━━━━━━━━━━━━━━━━━━

🎯 ENTRY
{entry:.2f}

🛑 STOP LOSS
{stop:.2f}

💰 TAKE PROFIT
{target:.2f}

📊 ATR
{atr:.2f}

🕐 CANDLE
{entry_time}

━━━━━━━━━━━━━━━━━━━━

🟢 PAPER TRADE
🔴 ORDINI REALI: NO

⚠️ Segnale generato
da Atlas AI.
"""


# ============================================================
# EXIT MESSAGE
# ============================================================

def format_exit(trade):

    entry = float(
        trade.get(
            "entry_price",
            0,
        )
    )

    exit_price = float(
        trade.get(
            "exit_price",
            0,
        )
    )

    pnl = float(
        trade.get(
            "pnl",
            0,
        )
    )

    return_pct = float(
        trade.get(
            "return_pct",
            0,
        )
    )

    reason = trade.get(
        "reason",
        "N/D",
    )

    if pnl > 0:

        result = "🟢 PROFITTO"

    elif pnl < 0:

        result = "🔴 PERDITA"

    else:

        result = "⚪ BREAK EVEN"

    return f"""
🔔 ATLAS AI TRADE CLOSED

XAU/USD

{result}

━━━━━━━━━━━━━━━━━━━━

ENTRY
{entry:.2f}

EXIT
{exit_price:.2f}

━━━━━━━━━━━━━━━━━━━━

💰 PnL
${pnl:+.2f}

📊 Return
{return_pct:+.2f}%

📌 Motivo
{reason}

━━━━━━━━━━━━━━━━━━━━

🟢 PAPER TRADING
🔴 ORDINI REALI: NO
"""


# ============================================================
# MONITOR
# ============================================================

def monitor():

    print()
    print(
        "========================================"
    )
    print(
        "ATLAS AI TELEGRAM ALERT MONITOR"
    )
    print(
        "========================================"
    )
    print()
    print(
        "🟢 Monitor avviato"
    )
    print(
        "📡 Metodo: Telegram Bot API HTTPS"
    )
    print(
        "🔔 Alert automatici: ATTIVI"
    )
    print()
    print(
        f"📄 State: {STATE_FILE}"
    )
    print()

    alert_state = load_alert_state()

    while True:

        try:

            state = load_paper_state()

            position = state.get(
                "position"
            )

            trades = state.get(
                "trades",
                [],
            )

            current_trade_count = len(
                trades
            )

            last_trade_count = int(
                alert_state.get(
                    "last_trade_count",
                    0,
                )
            )

            last_position_id = (
                alert_state.get(
                    "last_position_id"
                )
            )

            # ==================================================
            # NUOVA POSIZIONE
            # ==================================================

            if position:

                current_position_id = (
                    get_position_id(
                        position
                    )
                )

                if (
                    current_position_id
                    != last_position_id
                ):

                    print()
                    print(
                        "🚨 NUOVA POSIZIONE"
                    )

                    message = format_entry(
                        position
                    )

                    success = telegram_send(
                        message
                    )

                    if success:

                        alert_state[
                            "last_position_id"
                        ] = (
                            current_position_id
                        )

                        save_json(
                            ALERT_STATE_FILE,
                            alert_state,
                        )

            else:

                if last_position_id is not None:

                    alert_state[
                        "last_position_id"
                    ] = None

                    save_json(
                        ALERT_STATE_FILE,
                        alert_state,
                    )

            # ==================================================
            # NUOVI TRADE CHIUSI
            # ==================================================

            if (
                current_trade_count
                > last_trade_count
            ):

                print()
                print(
                    "🔔 NUOVI TRADE CHIUSI: "
                    f"{current_trade_count - last_trade_count}"
                )

                new_trades = trades[
                    last_trade_count:
                ]

                all_sent = True

                for trade in new_trades:

                    success = telegram_send(
                        format_exit(
                            trade
                        )
                    )

                    if not success:

                        all_sent = False

                        break

                if all_sent:

                    alert_state[
                        "last_trade_count"
                    ] = (
                        current_trade_count
                    )

                    save_json(
                        ALERT_STATE_FILE,
                        alert_state,
                    )

            # ==================================================
            # STORICO RESETTATO
            # ==================================================

            elif (
                current_trade_count
                < last_trade_count
            ):

                print(
                    "ℹ️ Storico trade "
                    "rilevato come resettato."
                )

                alert_state[
                    "last_trade_count"
                ] = current_trade_count

                save_json(
                    ALERT_STATE_FILE,
                    alert_state,
                )

        except KeyboardInterrupt:

            print()
            print(
                "🛑 Monitor fermato."
            )

            break

        except Exception as error:

            print()
            print(
                "⚠️ ERRORE MONITOR"
            )

            print(error)

            print(
                "Il monitor continuerà."
            )

        time.sleep(
            POLL_SECONDS
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    monitor()