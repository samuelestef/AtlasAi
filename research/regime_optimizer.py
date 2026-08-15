"""
Atlas AI
XAU/USD Regime Filter Optimizer
"""

from backtesting import Backtest

from research import config
from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy
from signals.atlas_signal_v2 import AtlasSignalV2


REGIME_VALUES = [
    0.90,
    0.95,
    1.00,
    1.05,
    1.10,
]

DEVELOPMENT_RATIO = 0.85


def run_backtest(df):

    bt = Backtest(
        df,
        AtlasBacktestStrategy,
        cash=10000,
        commission=0.0002,
        exclusive_orders=True,
        finalize_trades=True,
    )

    return bt.run()


def main():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD REGIME OPTIMIZER")
    print("========================================")

    df = ResearchLoader().load()

    df = df.dropna().copy()

    total = len(df)

    development_size = int(
        total * DEVELOPMENT_RATIO
    )

    development = df.iloc[
        :development_size
    ].copy()

    print()
    print(
        f"Candele totali       : {total}"
    )

    print(
        f"Candele sviluppo    : "
        f"{len(development)}"
    )

    print(
        f"FINAL HOLDOUT        : "
        f"{total - len(development)}"
    )

    print()
    print("FINAL HOLDOUT BLOCCATO")
    print("========================================")

    results = []

    for regime in REGIME_VALUES:

        config.ATR_REGIME_MIN_RATIO = regime

        stats = run_backtest(
            development
        )

        pf = stats["Profit Factor"]

        if pf != pf:
            pf = 0.0

        results.append(
            {
                "regime": regime,
                "return": float(
                    stats["Return [%]"]
                ),
                "pf": float(pf),
                "win": float(
                    stats["Win Rate [%]"]
                ),
                "drawdown": float(
                    stats["Max. Drawdown [%]"]
                ),
                "trades": int(
                    stats["# Trades"]
                ),
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
    print("============== RISULTATI ==============")

    for index, result in enumerate(
        results,
        1
    ):

        print()
        print(f"#{index}")

        print(
            f"Regime        : "
            f"{result['regime']:.2f}"
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

    best = results[0]

    print()
    print("========================================")
    print("MIGLIORE CONFIGURAZIONE DEVELOPMENT")
    print("========================================")

    print(
        f"ATR regime : "
        f"{best['regime']:.2f}"
    )

    print(
        f"Return     : "
        f"{best['return']:.2f}%"
    )

    print(
        f"PF         : "
        f"{best['pf']:.3f}"
    )

    print(
        f"Trades     : "
        f"{best['trades']}"
    )

    print()
    print("========================================")
    print(
        "Il FINAL HOLDOUT NON è stato utilizzato."
    )
    print("========================================")


if __name__ == "__main__":
    main()