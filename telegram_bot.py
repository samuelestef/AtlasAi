import os
import json
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ============================================================
# ATLAS AI TELEGRAM BOT
# ============================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_DIR = Path(__file__).resolve().parent

STATE_DIR = Path(os.getenv("ATLAS_STATE_DIR") or BASE_DIR)

STATE_FILE = STATE_DIR / "active_m15_state.json"
ALERT_STATE_FILE = STATE_DIR / "telegram_alert_state.json"

MONITOR_SECONDS = 5

INITIAL_CAPITAL = 10000.0


# ============================================================
# DEFAULT STATE
# ============================================================

def default_state():

    return {
        "balance": INITIAL_CAPITAL,
        "equity": INITIAL_CAPITAL,
        "trades": [],
        "position": None,
    }


# ============================================================
# LOAD PAPER STATE
# ============================================================

def load_state():

    if not STATE_FILE.exists():
        return default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"⚠️ Impossibile leggere active_m15_state.json: {error}"
        )

        return default_state()


# ============================================================
# LOAD TELEGRAM ALERT STATE
# ============================================================

def load_alert_state():

    if not ALERT_STATE_FILE.exists():

        return {
            "last_trade_count": 0,
            "last_position_id": None,
        }

    try:

        with open(
            ALERT_STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception:

        return {
            "last_trade_count": 0,
            "last_position_id": None,
        }


# ============================================================
# SAVE TELEGRAM ALERT STATE
# ============================================================

def save_alert_state(state):

    try:

        with open(
            ALERT_STATE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                state,
                file,
                indent=2,
            )

    except Exception as error:

        print(
            f"⚠️ Impossibile salvare alert state: {error}"
        )


# ============================================================
# TELEGRAM SEND WITH RETRY
# ============================================================

async def send_alert(
    bot,
    text,
):

    if not CHAT_ID:

        print(
            "❌ TELEGRAM_CHAT_ID non configurato."
        )

        return False

    max_attempts = 5

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        try:

            await bot.send_message(
                chat_id=int(CHAT_ID),
                text=text,
            )

            print(
                "📨 Telegram: messaggio inviato."
            )

            return True

        except Exception as error:

            print()
            print(
                f"⚠️ Telegram non raggiungibile "
                f"(tentativo {attempt}/{max_attempts})"
            )

            print(error)

            if attempt < max_attempts:

                await asyncio.sleep(
                    5 * attempt
                )

    print(
        "❌ Impossibile inviare il messaggio Telegram."
    )

    return False


# ============================================================
# POSITION ID
# ============================================================

def get_position_id(position):

    if not position:
        return None

    entry_time = position.get(
        "entry_time"
    )

    entry_price = position.get(
        "entry_price"
    )

    return (
        f"{entry_time}|"
        f"{entry_price}"
    )


# ============================================================
# FORMAT ENTRY
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

    direction = position.get(
        "direction",
        "LONG",
    )

    stop = float(
        position.get(
            "stop_price",
            entry - atr * 1.2
            if direction == "LONG"
            else entry + atr * 1.2,
        )
    )

    target = float(
        position.get(
            "take_price",
            entry + atr * 1.5
            if direction == "LONG"
            else entry - atr * 1.5,
        )
    )

    entry_time = position.get(
        "entry_time",
        "N/D",
    )

    side_emoji = (
        "🟢" if direction == "LONG" else "🔴"
    )

    return f"""
🚨 ATLAS AI SIGNAL

XAU/USD

{side_emoji} {direction}

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

📊 Segnale registrato nello storico Atlas AI.
🔬 Ambiente: Paper Trading.
"""


# ============================================================
# FORMAT EXIT
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

📊 Trade registrato nello storico Atlas AI.
🔬 Ambiente: Paper Trading.
"""


# ============================================================
# MONITOR STATE
# ============================================================

async def monitor_state(
    application,
):

    print(
        "📡 Atlas Telegram Monitor attivo"
    )

    alert_state = load_alert_state()

    while True:

        try:

            state = load_state()

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
                        "🚨 NUOVA POSIZIONE RILEVATA"
                    )

                    success = await send_alert(
                        application.bot,
                        format_entry(
                            position
                        ),
                    )

                    if success:

                        alert_state[
                            "last_position_id"
                        ] = current_position_id

                        save_alert_state(
                            alert_state
                        )

            else:

                if last_position_id is not None:

                    alert_state[
                        "last_position_id"
                    ] = None

                    save_alert_state(
                        alert_state
                    )

            # ==================================================
            # NUOVI TRADE CHIUSI
            # ==================================================

            if (
                current_trade_count
                > last_trade_count
            ):

                new_trades = trades[
                    last_trade_count:
                ]

                print()
                print(
                    f"🔔 Nuovi trade chiusi: "
                    f"{len(new_trades)}"
                )

                all_sent = True

                for trade in new_trades:

                    success = await send_alert(
                        application.bot,
                        format_exit(
                            trade
                        ),
                    )

                    if not success:

                        all_sent = False

                        break

                if all_sent:

                    alert_state[
                        "last_trade_count"
                    ] = current_trade_count

                    save_alert_state(
                        alert_state
                    )

            elif (
                current_trade_count
                < last_trade_count
            ):

                # Lo storico è stato azzerato.
                # Sincronizziamo il contatore.

                alert_state[
                    "last_trade_count"
                ] = current_trade_count

                save_alert_state(
                    alert_state
                )

        except Exception as error:

            print()
            print(
                "⚠️ ERRORE MONITOR TELEGRAM"
            )

            print(error)

            print(
                "Atlas continuerà a ritentare."
            )

        await asyncio.sleep(
            MONITOR_SECONDS
        )


# ============================================================
# TEST ALERT
# ============================================================

async def testalert(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = """
🧪 ATLAS AI TEST ALERT

Telegram è collegato correttamente.

━━━━━━━━━━━━━━━━━━━━

🟢 Bot: ONLINE
🟢 Chat ID: OK
🟢 Alert: OK

Ambiente:
🟢 PAPER TRADING

Storico:
🟢 ATTIVO
"""

    await update.message.reply_text(
        text
    )


# ============================================================
# ATLAS AI MENU
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 RISULTATI",
                callback_data="menu_results",
            ),
            InlineKeyboardButton(
                "📡 CANALE TELEGRAM",
                url="https://t.me/atlasaitrading",
            ),
        ],
        [
            InlineKeyboardButton(
                "🤖 COME FUNZIONA",
                callback_data="menu_how",
            ),
            InlineKeyboardButton(
                "🔬 SYSTEM STATUS",
                callback_data="menu_test",
            ),
        ],
        [
            InlineKeyboardButton(
                "ℹ️ INFO ATLAS",
                callback_data="menu_about",
            ),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    text = """
🧠 ATLAS AI

QUANTITATIVE TRADING INTELLIGENCE

━━━━━━━━━━━━━━━━━━━━

Atlas AI è un sistema quantitativo
dedicato all'analisi di XAU/USD.

Il sistema genera segnali secondo
regole definite e registra ogni
operazione.

🔬 STATO ATTUALE
🟢 SISTEMA ATTIVO

📊 Storico pubblico
🤖 Segnali automatici
🔬 Paper Trading

Il sistema registra ogni operazione,
inclusi profitti, perdite e timeout.

👇 SCEGLI COSA VUOI VEDERE
"""

    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
    )


# ============================================================
# CALLBACK MENU
# ============================================================

async def menu_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    if query.data == "menu_results":

        state = load_state()

        trades = state.get(
            "trades",
            [],
        )

        balance = float(
            state.get(
                "balance",
                INITIAL_CAPITAL,
            )
        )

        total = len(trades)

        wins = 0
        losses = 0
        timeouts = 0
        pnl_total = 0.0

        for trade in trades:

            pnl = float(
                trade.get(
                    "pnl",
                    0,
                )
            )

            pnl_total += pnl

            if pnl > 0:
                wins += 1
            elif pnl < 0:
                losses += 1

            if str(
                trade.get("reason", "")
            ).upper() == "TIMEOUT":
                timeouts += 1

        if total > 0:

            win_rate = (
                wins
                / total
                * 100
            )

        else:

            win_rate = 0.0

        return_pct = (
            balance
            - INITIAL_CAPITAL
        ) / INITIAL_CAPITAL * 100

        text = f"""
📊 ATLAS AI RESULTS

━━━━━━━━━━━━━━━━━━━━

Trades chiusi
{total}

🟢 Profit
{wins}

🔴 Loss
{losses}

🟡 Timeout
{timeouts}

🎯 Win Rate
{win_rate:.2f}%

💰 PnL
${pnl_total:+,.2f}

📈 Return
{return_pct:+.2f}%

💵 Equity
${balance:,.2f}

━━━━━━━━━━━━━━━━━━━━

📊 Trade registrato nello storico Atlas AI.
🔬 Ambiente: Paper Trading.

⚠️ I risultati sono relativi
al paper trading e non garantiscono
risultati futuri.
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 INDIETRO",
                    callback_data="menu_home",
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    if query.data == "menu_how":

        text = """
🤖 COME FUNZIONA ATLAS

━━━━━━━━━━━━━━━━━━━━

Atlas AI analizza XAU/USD
utilizzando una strategia quantitativa.

Il sistema valuta diversi elementi
del mercato e, quando le condizioni
sono soddisfatte, genera un segnale.

📊 Il sistema registra:

• Entry
• Stop Loss
• Take Profit
• Exit
• PnL
• Motivo della chiusura

━━━━━━━━━━━━━━━━━━━━

🔬 Ogni operazione viene registrata
nello storico.

Non vengono mostrati soltanto
i trade positivi.

🟢 Profit
🔴 Loss
🟡 Timeout

━━━━━━━━━━━━━━━━━━━━

📊 Trade registrato nello storico Atlas AI.
🔬 Ambiente: Paper Trading.
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 INDIETRO",
                    callback_data="menu_home",
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    if query.data == "menu_test":

        state = load_state()

        trades = state.get(
            "trades",
            [],
        )

        position = state.get(
            "position"
        )

        if position:

            position_text = "🟢 POSIZIONE APERTA"

        else:

            position_text = "⚪ FLAT"

        text = f"""
🔬 ATLAS AI — SYSTEM STATUS

━━━━━━━━━━━━━━━━━━━━

Stato sistema
🟢 ATTIVO

Ambiente
🟢 PAPER TRADING

Trade chiusi
{len(trades)}

Posizione
{position_text}

━━━━━━━━━━━━━━━━━━━━

Atlas sta costruendo uno storico
operativo per valutare la strategia
nel tempo.

⚠️ Lo storico non costituisce una
garanzia di rendimento futuro.
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 INDIETRO",
                    callback_data="menu_home",
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    if query.data == "menu_about":

        text = """
ℹ️ ATLAS AI

━━━━━━━━━━━━━━━━━━━━

Sistema quantitativo dedicato
all'analisi di XAU/USD.

Atlas utilizza indicatori e regole
quantitative per identificare
possibili condizioni operative.

━━━━━━━━━━━━━━━━━━━━

📊 Trade registrato nello storico Atlas AI.
🔬 Ambiente: Paper Trading.

━━━━━━━━━━━━━━━━━━━━

L'obiettivo è raccogliere dati,
misurare le performance e valutare
la strategia attraverso uno storico
trasparente.

⚠️ Atlas AI non garantisce
rendimenti futuri.
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 INDIETRO",
                    callback_data="menu_home",
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    if query.data == "menu_home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 RISULTATI",
                    callback_data="menu_results",
                ),
                InlineKeyboardButton(
                    "📡 CANALE TELEGRAM",
                    url="https://t.me/atlasaitrading",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🤖 COME FUNZIONA",
                    callback_data="menu_how",
                ),
                InlineKeyboardButton(
                    "🔬 SYSTEM STATUS",
                    callback_data="menu_test",
                ),
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ INFO ATLAS",
                    callback_data="menu_about",
                ),
            ],
        ]

        text = """
🧠 ATLAS AI

QUANTITATIVE TRADING INTELLIGENCE

━━━━━━━━━━━━━━━━━━━━

Atlas AI è un sistema quantitativo
dedicato all'analisi di XAU/USD.

🔬 STATO ATTUALE
🟢 SISTEMA ATTIVO

━━━━━━━━━━━━━━━━━━━━

📊 Storico pubblico
🤖 Sistema automatico
🔬 Paper Trading

👇 SCEGLI COSA VUOI VEDERE
"""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return


# ============================================================
# /CHATID
# ============================================================

async def chatid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    current_chat_id = (
        update.effective_chat.id
    )

    text = f"""
🆔 ATLAS CHAT ID

Il tuo Chat ID è:

{current_chat_id}

Configurato:
🟢
"""

    await update.message.reply_text(
        text
    )


# ============================================================
# /STATUS
# ============================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    state = load_state()

    balance = float(
        state.get(
            "balance",
            INITIAL_CAPITAL,
        )
    )

    equity = float(
        state.get(
            "equity",
            balance,
        )
    )

    trades = state.get(
        "trades",
        [],
    )

    position = state.get(
        "position"
    )

    if position:

        direction = position.get(
            "direction",
            "N/D",
        )

        entry = float(
            position.get(
                "entry_price",
                0,
            )
        )

        stop = float(
            position.get(
                "stop_price",
                0,
            )
        )

        target = float(
            position.get(
                "take_price",
                0,
            )
        )

        side_emoji = (
            "🟢" if direction == "LONG" else "🔴"
        )

        position_text = (
            f"{side_emoji} {direction}\n"
            f"Entry: {entry:.2f}\n"
            f"SL: {stop:.2f}\n"
            f"TP: {target:.2f}"
        )

    else:

        position_text = "⚪ FLAT"

    text = f"""
🤖 ATLAS AI
XAU/USD

━━━━━━━━━━━━━━━━━━━━

💰 Balance
${balance:,.2f}

📊 Equity
${equity:,.2f}

📈 Trade chiusi
{len(trades)}

📍 Posizione
{position_text}

━━━━━━━━━━━━━━━━━━━━

🔔 Alert Telegram: 🟢
🔬 Ambiente: PAPER TRADING
"""

    await update.message.reply_text(
        text
    )


# ============================================================
# /PERFORMANCE
# ============================================================

async def performance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    state = load_state()

    balance = float(
        state.get(
            "balance",
            INITIAL_CAPITAL,
        )
    )

    trades = state.get(
        "trades",
        [],
    )

    total = len(
        trades
    )

    if total == 0:

        await update.message.reply_text(
            """
📈 ATLAS AI PERFORMANCE

Nessun trade chiuso.

🔔 Monitor attivo.
"""
        )

        return

    wins = 0
    losses = 0
    pnl_total = 0.0

    for trade in trades:

        pnl = float(
            trade.get(
                "pnl",
                0,
            )
        )

        pnl_total += pnl

        if pnl > 0:

            wins += 1

        elif pnl < 0:

            losses += 1

    win_rate = (
        wins
        / total
        * 100
    )

    return_pct = (
        balance
        - INITIAL_CAPITAL
    ) / INITIAL_CAPITAL * 100

    text = f"""
📈 ATLAS AI PERFORMANCE

━━━━━━━━━━━━━━━━━━━━

Trades
{total}

🟢 Win
{wins}

🔴 Loss
{losses}

🎯 Win Rate
{win_rate:.2f}%

💰 PnL
${pnl_total:+,.2f}

📊 Return
{return_pct:+.2f}%

💵 Equity
${balance:,.2f}

━━━━━━━━━━━━━━━━━━━━

🔬 Ambiente: Paper Trading
⚠️ Lo storico non garantisce
risultati futuri.
"""

    await update.message.reply_text(
        text
    )


# ============================================================
# /PRO
# ============================================================

async def pro(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        """
💎 ATLAS PRO

Accesso premium ai segnali
e alle funzionalità avanzate
di Atlas AI.

━━━━━━━━━━━━━━━━━━━━

🟢 Segnali LONG / SHORT
🎯 Entry
🛑 Stop Loss
💰 Take Profit
📊 Performance
🔔 Alert Telegram

━━━━━━━━━━━━━━━━━━━━

🚀 ATLAS PRO

Disponibile prossimamente.

Stiamo completando la struttura
commerciale e l'attivazione
degli accessi.

━━━━━━━━━━━━━━━━━━━━

⚠️ Atlas è uno strumento
di analisi e non garantisce
profitti futuri.
"""
    )


# ============================================================
# /ABOUT
# ============================================================

async def about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        """
ℹ️ ATLAS AI

Sistema quantitativo per
l'analisi di XAU/USD.

Indicatori:

• EMA
• RSI
• ATR
• ADX
• DI+ / DI-

🔬 Ambiente: Paper Trading

⚠️ Nessuna garanzia
di rendimento futuro.
"""
    )


# ============================================================
# POST INIT
# ============================================================

async def post_init(
    application,
):

    # IMPORTANTE:
    # usiamo asyncio.create_task()
    # e NON Application.create_task()
    # per evitare il warning PTB.

    asyncio.create_task(
        monitor_state(
            application
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN "
            "non trovato nel file .env"
        )

    if not CHAT_ID:

        raise RuntimeError(
            "TELEGRAM_CHAT_ID "
            "non trovato nel file .env"
        )

    print()
    print(
        "========================================"
    )
    print(
        "ATLAS AI TELEGRAM BOT"
    )
    print(
        "========================================"
    )
    print()
    print(
        "🟢 Bot avviato"
    )
    print(
        "📡 Telegram monitor attivo"
    )
    print(
        "🔔 Alert automatici attivi"
    )
    print(
        "🎛️ Menu interattivo attivo"
    )
    print()

    application = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    # ========================================================
    # COMMANDS
    # ========================================================

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "chatid",
            chatid,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status,
        )
    )

    application.add_handler(
        CommandHandler(
            "performance",
            performance,
        )
    )

    application.add_handler(
        CommandHandler(
            "testalert",
            testalert,
        )
    )

    application.add_handler(
        CommandHandler(
            "pro",
            pro,
        )
    )

    application.add_handler(
        CommandHandler(
            "about",
            about,
        )
    )

    # ========================================================
    # INLINE MENU CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            menu_callback,
        )
    )

    # ========================================================
    # START BOT
    # ========================================================

    application.run_polling(
        drop_pending_updates=True
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()