"""
Atlas AI
XAU/USD Final Holdout - ADX Regime
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

FINAL_HOLDOUT_RATIO = 0.15

COMMISSION = 0.0002


def apply_parameters():

    AtlasSignalV2.LOOKBACK = LOOKBACK
    AtlasSignalV2.RSI_MIN = RSI_MIN

    config.STOP_ATR = STOP_ATR
    config.TAKE_ATR = TAKE_ATR


def main():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD FINAL HOLDOUT")
    print("ADX REGIME VERSION")
    print("========================================")

    df = ResearchLoader().load()

    df = df.dropna().copy()

    total = len(df)

    holdout_size = int(
        total * FINAL_HOLDOUT_RATIO
    )

    holdout = df.iloc[
        -holdout_size:
    ].copy()

    apply_parameters()

    print()
    print(
        f"Candele totali      : {total}"
    )

    print(
        f"Candele FINAL TEST  : "
        f"{len(holdout)}"
    )

    print()
    print("========================================")
    print("PARAMETRI BLOCCATI")
    print("========================================")

    print(f"Lookback : {LOOKBACK}")
    print(f"RSI      : {RSI_MIN}")
    print(f"Stop ATR : {STOP_ATR}")
    print(f"Take ATR : {TAKE_ATR}")
    print("ADX      : >= 25")
    print("DI+      : > DI-")

    print()
    print("========================================")
    print("FINAL HOLDOUT")
    print("========================================")

    bt = Backtest(
        holdout,
        AtlasBacktestStrategy,
        cash=10000,
        commission=COMMISSION,
        exclusive_orders=True,
        finalize_trades=True,
    )

    stats = bt.run()

    pf = stats["Profit Factor"]

    if pf != pf:
        pf = 0.0

    print()
    print(
        f"Trades        : "
        f"{stats['# Trades']}"
    )

    print(
        f"Win Rate      : "
        f"{stats['Win Rate [%]']:.2f}%"
    )

    print(
        f"Return        : "
        f"{stats['Return [%]']:.2f}%"
    )

    print(
        f"Profit Factor : "
        f"{pf:.3f}"
    )

    print(
        f"Drawdown      : "
        f"{stats['Max. Drawdown [%]']:.2f}%"
    )

    print(
        f"Equity Finale : "
        f"${stats['Equity Final [$]']:.2f}"
    )

    print()
    print("========================================")
    print("VERDETTO")
    print("========================================")

    if (
        stats["# Trades"] >= 20
        and stats["Return [%]"] > 0
        and pf >= 1.0
    ):
        print("PASS")
        print(
            "ADX REGIME supera il FINAL HOLDOUT."
        )
    else:
        print("FAIL")
        print(
            "ADX REGIME non supera "
            "il FINAL HOLDOUT."
        )

    print("========================================")


if __name__ == "__main__":
    main()