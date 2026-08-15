"""
Atlas AI
XAU/USD Rolling Validation
PARAMETRI BLOCCATI - ADX REGIME
"""

from backtesting import Backtest

from research import config
from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy
from signals.atlas_signal_v2 import AtlasSignalV2


LOOKBACK = 20
RSI_MIN = 55

STOP_ATR = 1.2
TAKE_ATR = 1.5

ADX_MIN = 25.0

COMMISSION = 0.0002

WINDOW_RATIO = 0.15


def apply_parameters():

    AtlasSignalV2.LOOKBACK = LOOKBACK
    AtlasSignalV2.RSI_MIN = RSI_MIN
    AtlasSignalV2.ADX_MIN = ADX_MIN

    config.STOP_ATR = STOP_ATR
    config.TAKE_ATR = TAKE_ATR


def run_backtest(df):

    bt = Backtest(
        df,
        AtlasBacktestStrategy,
        cash=10000,
        commission=COMMISSION,
        exclusive_orders=True,
        finalize_trades=True,
    )

    return bt.run()


def main():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD ROLLING VALIDATION")
    print("ADX REGIME - PARAMETRI BLOCCATI")
    print("========================================")

    df = ResearchLoader().load()

    df = df.dropna().copy()

    apply_parameters()

    total = len(df)

    window_size = int(
        total * WINDOW_RATIO
    )

    print()
    print(
        f"Candele totali : {total}"
    )

    print(
        f"Dimensione finestra : "
        f"{window_size}"
    )

    print()
    print("========================================")
    print("PARAMETRI")
    print("========================================")

    print(f"Lookback : {LOOKBACK}")
    print(f"RSI      : {RSI_MIN}")
    print(f"Stop ATR : {STOP_ATR}")
    print(f"Take ATR : {TAKE_ATR}")
    print(f"ADX      : >= {ADX_MIN}")

    results = []

    # Quattro finestre consecutive.
    # Nessuna ottimizzazione viene eseguita.
    for i in range(4):

        start = total - (
            (4 - i) * window_size
        )

        end = start + window_size

        window = df.iloc[
            start:end
        ].copy()

        stats = run_backtest(window)

        pf = stats["Profit Factor"]

        if pf != pf:
            pf = 0.0

        result = {
            "window": i + 1,
            "start": start,
            "end": end,
            "trades": int(
                stats["# Trades"]
            ),
            "win": float(
                stats["Win Rate [%]"]
            ),
            "return": float(
                stats["Return [%]"]
            ),
            "pf": float(pf),
            "drawdown": float(
                stats["Max. Drawdown [%]"]
            ),
        }

        results.append(result)

        print()
        print(
            f"========== WINDOW {i + 1} =========="
        )

        print(
            f"Bar : {start} → {end}"
        )

        print(
            f"Trades        : "
            f"{result['trades']}"
        )

        print(
            f"Win Rate      : "
            f"{result['win']:.2f}%"
        )

        print(
            f"Return        : "
            f"{result['return']:.2f}%"
        )

        print(
            f"Profit Factor : "
            f"{result['pf']:.3f}"
        )

        print(
            f"Drawdown      : "
            f"{result['drawdown']:.2f}%"
        )

    positive = sum(
        1
        for r in results
        if r["return"] > 0
        and r["pf"] >= 1.0
    )

    total_return = sum(
        r["return"]
        for r in results
    )

    average_return = (
        total_return / len(results)
    )

    print()
    print("----------------------------------------")

    print(
        f"Finestre positive : "
        f"{positive}/4"
    )

    print(
        f"Return medio      : "
        f"{average_return:.2f}%"
    )

    print(
        f"Return totale*    : "
        f"{total_return:.2f}%"
    )

    print("----------------------------------------")

    print()
    print("========================================")
    print("VERDETTO")
    print("========================================")

    if positive == 4:

        print(
            "PASS FORTE"
        )

        print(
            "Tutte le finestre rolling "
            "sono positive."
        )

    elif positive >= 3:

        print(
            "PASS"
        )

        print(
            "La strategia mantiene "
            "robustezza nella maggioranza "
            "delle finestre."
        )

    elif positive >= 2:

        print(
            "INTERMEDIO"
        )

        print(
            "Robustezza parziale."
        )

    else:

        print(
            "FAIL"
        )

        print(
            "La strategia non mantiene "
            "robustezza temporale."
        )

    print()
    print("* Somma dei return delle finestre;")
    print("  non rappresenta il rendimento")
    print("  composto di un unico conto.")
    print("========================================")


if __name__ == "__main__":
    main()