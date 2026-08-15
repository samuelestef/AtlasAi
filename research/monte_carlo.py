"""
Atlas AI
XAU/USD Monte Carlo Bootstrap
"""

import numpy as np

from backtesting import Backtest

from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy


INITIAL_CAPITAL = 10000

COMMISSION = 0.0002

SIMULATIONS = 5000

RANDOM_SEED = 42


def run_backtest(df):

    bt = Backtest(
        df,
        AtlasBacktestStrategy,
        cash=INITIAL_CAPITAL,
        commission=COMMISSION,
        exclusive_orders=True,
        finalize_trades=True,
    )

    return bt.run()


def simulate_bootstrap(
    returns,
    initial_capital,
):

    sample = np.random.choice(
        returns,
        size=len(returns),
        replace=True,
    )

    equity = initial_capital

    peak = equity

    max_drawdown = 0.0

    for trade_return in sample:

        equity *= (
            1.0 + trade_return
        )

        if equity > peak:

            peak = equity

        drawdown = (
            equity - peak
        ) / peak

        if drawdown < max_drawdown:

            max_drawdown = drawdown

    return equity, max_drawdown


def main():

    print()
    print("========================================")
    print("ATLAS AI XAU/USD MONTE CARLO BOOTSTRAP")
    print("========================================")

    np.random.seed(RANDOM_SEED)

    df = ResearchLoader().load()

    df = df.dropna().copy()

    print()
    print(
        f"Candele disponibili : {len(df)}"
    )

    stats = run_backtest(df)

    trades = stats["_trades"]

    if trades.empty:

        print()
        print("Nessun trade trovato.")

        return

    returns = (
        trades["ReturnPct"]
        .astype(float)
        .to_numpy()
    )

    print()
    print("============== BACKTEST ==============")

    print(
        f"Trades        : "
        f"{len(returns)}"
    )

    print(
        f"Return        : "
        f"{stats['Return [%]']:.2f}%"
    )

    print(
        f"Profit Factor : "
        f"{stats['Profit Factor']:.3f}"
    )

    print(
        f"Drawdown      : "
        f"{stats['Max. Drawdown [%]']:.2f}%"
    )

    final_equities = []
    drawdowns = []

    for _ in range(SIMULATIONS):

        equity, drawdown = simulate_bootstrap(
            returns,
            INITIAL_CAPITAL,
        )

        final_equities.append(equity)
        drawdowns.append(drawdown)

    final_equities = np.array(
        final_equities
    )

    drawdowns = np.array(
        drawdowns
    )

    returns_pct = (
        final_equities
        / INITIAL_CAPITAL
        - 1.0
    ) * 100.0

    drawdowns_pct = drawdowns * 100.0

    probability_profit = (
        np.mean(
            final_equities
            > INITIAL_CAPITAL
        )
        * 100.0
    )

    probability_loss_5 = (
        np.mean(
            final_equities
            < INITIAL_CAPITAL * 0.95
        )
        * 100.0
    )

    probability_loss_10 = (
        np.mean(
            final_equities
            < INITIAL_CAPITAL * 0.90
        )
        * 100.0
    )

    print()
    print("=========== MONTE CARLO ===========")

    print(
        f"Simulazioni            : "
        f"{SIMULATIONS}"
    )

    print(
        f"Probabilità profitto   : "
        f"{probability_profit:.2f}%"
    )

    print(
        f"Probabilità perdita >5%  : "
        f"{probability_loss_5:.2f}%"
    )

    print(
        f"Probabilità perdita >10% : "
        f"{probability_loss_10:.2f}%"
    )

    print()
    print("------ EQUITY FINALE ------")

    print(
        f"Peggiore       : "
        f"${final_equities.min():.2f}"
    )

    print(
        f"5° percentile  : "
        f"${np.percentile(final_equities, 5):.2f}"
    )

    print(
        f"Mediana        : "
        f"${np.median(final_equities):.2f}"
    )

    print(
        f"95° percentile : "
        f"${np.percentile(final_equities, 95):.2f}"
    )

    print(
        f"Migliore       : "
        f"${final_equities.max():.2f}"
    )

    print()
    print("------ RETURN ------")

    print(
        f"Peggiore       : "
        f"{returns_pct.min():.2f}%"
    )

    print(
        f"5° percentile  : "
        f"{np.percentile(returns_pct, 5):.2f}%"
    )

    print(
        f"Mediana        : "
        f"{np.median(returns_pct):.2f}%"
    )

    print(
        f"95° percentile : "
        f"{np.percentile(returns_pct, 95):.2f}%"
    )

    print(
        f"Migliore       : "
        f"{returns_pct.max():.2f}%"
    )

    print()
    print("------ MAX DRAWDOWN ------")

    print(
        f"Peggiore       : "
        f"{drawdowns_pct.min():.2f}%"
    )

    print(
        f"5° percentile  : "
        f"{np.percentile(drawdowns_pct, 5):.2f}%"
    )

    print(
        f"Mediana        : "
        f"{np.median(drawdowns_pct):.2f}%"
    )

    print(
        f"95° percentile : "
        f"{np.percentile(drawdowns_pct, 95):.2f}%"
    )

    print(
        f"Migliore       : "
        f"{drawdowns_pct.max():.2f}%"
    )

    print()
    print("========================================")

    if probability_profit >= 70:

        print(
            "VERDETTO: MONTE CARLO PROMETTENTE"
        )

    elif probability_profit >= 50:

        print(
            "VERDETTO: MONTE CARLO INTERMEDIO"
        )

    else:

        print(
            "VERDETTO: MONTE CARLO DEBOLE"
        )

    print("========================================")


if __name__ == "__main__":
    main()