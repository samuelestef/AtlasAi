"""
Atlas AI
XAU/USD Multi-Window Walk Forward
"""

from backtesting import Backtest

from research import config
from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy
from signals.atlas_signal_v2 import AtlasSignalV2


# Configurazione candidata scelta dal TRAIN
LOOKBACK = 20
RSI_MIN = 55
STOP_ATR = 1.2
TAKE_ATR = 1.5


def apply_parameters():

    AtlasSignalV2.LOOKBACK = LOOKBACK
    AtlasSignalV2.RSI_MIN = RSI_MIN

    config.STOP_ATR = STOP_ATR
    config.TAKE_ATR = TAKE_ATR


def run_backtest(df, commission):

    bt = Backtest(
        df,
        AtlasBacktestStrategy,
        cash=10000,
        commission=commission,
        exclusive_orders=True,
        finalize_trades=True,
    )

    return bt.run()


def print_result(name, stats):

    pf = stats["Profit Factor"]

    if pf != pf:
        pf = 0.0

    print()
    print(name)
    print("----------------------------------------")
    print(f"Trades        : {stats['# Trades']}")
    print(f"Win Rate      : {stats['Win Rate [%]']:.2f}%")
    print(f"Return        : {stats['Return [%]']:.2f}%")
    print(f"Profit Factor : {pf:.3f}")
    print(
        f"Drawdown      : "
        f"{stats['Max. Drawdown [%]']:.2f}%"
    )


def run():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD MULTI-WINDOW TEST")
    print("========================================")

    df = ResearchLoader().load()

    df = df.dropna().copy()

    apply_parameters()

    total = len(df)

    print()
    print(f"Candele disponibili : {total}")

    print()
    print("PARAMETRI")
    print("----------------------------------------")
    print(f"Lookback : {LOOKBACK}")
    print(f"RSI      : {RSI_MIN}")
    print(f"Stop ATR : {STOP_ATR}")
    print(f"Take ATR : {TAKE_ATR}")

    # ==================================================
    # 4 finestre consecutive
    # ==================================================

    windows = [
        (0.00, 0.25, 0.25, 0.4375),
        (0.1875, 0.4375, 0.4375, 0.625),
        (0.375, 0.625, 0.625, 0.8125),
        (0.5625, 0.8125, 0.8125, 1.00),
    ]

    results = []

    for index, (
        train_start_pct,
        train_end_pct,
        test_start_pct,
        test_end_pct,
    ) in enumerate(windows, 1):

        train_start = int(
            total * train_start_pct
        )

        train_end = int(
            total * train_end_pct
        )

        test_start = int(
            total * test_start_pct
        )

        test_end = int(
            total * test_end_pct
        )

        train = df.iloc[
            train_start:train_end
        ].copy()

        test = df.iloc[
            test_start:test_end
        ].copy()

        print()
        print("========================================")
        print(f"WINDOW {index}")
        print("========================================")

        print(
            f"TRAIN : {len(train)} candele"
        )

        print(
            f"TEST  : {len(test)} candele"
        )

        stats = run_backtest(
            test,
            commission=0.0002,
        )

        print_result(
            "OUT-OF-SAMPLE",
            stats,
        )

        pf = stats["Profit Factor"]

        if pf != pf:
            pf = 0.0

        results.append(
            {
                "return": float(
                    stats["Return [%]"]
                ),
                "pf": float(pf),
                "trades": int(
                    stats["# Trades"]
                ),
                "drawdown": float(
                    stats["Max. Drawdown [%]"]
                ),
            }
        )

    # ==================================================
    # RIEPILOGO
    # ==================================================

    print()
    print("========================================")
    print("RIEPILOGO MULTI-WINDOW")
    print("========================================")

    positive = 0

    total_return = 0.0

    for index, result in enumerate(
        results,
        1
    ):

        print()
        print(
            f"Window {index} | "
            f"Return {result['return']:.2f}% | "
            f"PF {result['pf']:.3f} | "
            f"Trades {result['trades']}"
        )

        total_return += result["return"]

        if (
            result["return"] > 0
            and result["pf"] >= 1.0
        ):
            positive += 1

    average_return = (
        total_return / len(results)
    )

    print()
    print("----------------------------------------")
    print(
        f"Finestre positive : "
        f"{positive}/{len(results)}"
    )

    print(
        f"Return medio      : "
        f"{average_return:.2f}%"
    )

    # ==================================================
    # COST STRESS TEST
    # ==================================================

    print()
    print("========================================")
    print("COST STRESS TEST")
    print("========================================")

    costs = [
        0.0002,
        0.0005,
        0.0010,
    ]

    for commission in costs:

        stats = run_backtest(
            df,
            commission=commission,
        )

        pf = stats["Profit Factor"]

        if pf != pf:
            pf = 0.0

        print()
        print(
            f"Commissione : "
            f"{commission}"
        )

        print(
            f"Return      : "
            f"{stats['Return [%]']:.2f}%"
        )

        print(
            f"PF          : "
            f"{pf:.3f}"
        )

        print(
            f"Trades      : "
            f"{stats['# Trades']}"
        )

        print(
            f"Drawdown    : "
            f"{stats['Max. Drawdown [%]']:.2f}%"
        )

    print()
    print("========================================")

    if positive >= 3:

        print("VERDETTO: ROBUSTEZZA PROMETTENTE")

    elif positive >= 2:

        print("VERDETTO: ROBUSTEZZA PARZIALE")

    else:

        print("VERDETTO: ROBUSTEZZA DEBOLE")

    print("========================================")


if __name__ == "__main__":
    run()