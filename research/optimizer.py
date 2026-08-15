"""
Atlas AI
XAU/USD Momentum Robustness Optimizer
"""

from itertools import product

from backtesting import Backtest

from research import config
from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy
from signals.atlas_signal_v2 import AtlasSignalV2


LOOKBACK_VALUES = [15, 20, 25]
RSI_VALUES = [50, 52, 55]
STOP_ATR_VALUES = [0.8, 1.0, 1.2]
TAKE_ATR_VALUES = [1.5, 2.0, 2.5]


def run():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD ROBUSTNESS TEST")
    print("========================================")

    df = ResearchLoader().load()

    df = df.dropna().copy()

    results = []

    total = 0

    for (
        lookback,
        rsi_min,
        stop_atr,
        take_atr,
    ) in product(
        LOOKBACK_VALUES,
        RSI_VALUES,
        STOP_ATR_VALUES,
        TAKE_ATR_VALUES,
    ):

        total += 1

        AtlasSignalV2.LOOKBACK = lookback
        AtlasSignalV2.RSI_MIN = rsi_min

        config.STOP_ATR = stop_atr
        config.TAKE_ATR = take_atr

        bt = Backtest(
            df,
            AtlasBacktestStrategy,
            cash=10000,
            commission=0.0002,
            exclusive_orders=True,
            finalize_trades=True,
        )

        stats = bt.run()

        pf = stats["Profit Factor"]

        if pf != pf:
            pf = 0.0

        results.append(
            {
                "return": float(stats["Return [%]"]),
                "pf": float(pf),
                "win": float(stats["Win Rate [%]"]),
                "drawdown": float(
                    stats["Max. Drawdown [%]"]
                ),
                "trades": int(stats["# Trades"]),
                "lookback": lookback,
                "rsi": rsi_min,
                "stop": stop_atr,
                "take": take_atr,
            }
        )

    results.sort(
        key=lambda x: (
            x["pf"],
            x["return"],
        ),
        reverse=True,
    )

    print()
    print("============== TOP 10 ==============")

    for index, result in enumerate(
        results[:10],
        1
    ):

        print()
        print(f"#{index}")

        print(
            f"Return        : "
            f"{result['return']:.2f}%"
        )

        print(
            f"Profit Factor : "
            f"{result['pf']:.3f}"
        )

        print(
            f"Win Rate      : "
            f"{result['win']:.2f}%"
        )

        print(
            f"Drawdown      : "
            f"{result['drawdown']:.2f}%"
        )

        print(
            f"Trades        : "
            f"{result['trades']}"
        )

        print(
            f"Lookback      : "
            f"{result['lookback']}"
        )

        print(
            f"RSI           : "
            f"{result['rsi']}"
        )

        print(
            f"Stop ATR      : "
            f"{result['stop']}"
        )

        print(
            f"Take ATR      : "
            f"{result['take']}"
        )

    print()
    print("=====================================")
    print(
        f"Configurazioni testate : {total}"
    )
    print("=====================================")


if __name__ == "__main__":
    run()