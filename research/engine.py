"""
Atlas AI
Research Engine
"""

from backtesting import Backtest

from research.loader import ResearchLoader
from backtest.adapter import AtlasBacktestStrategy


class ResearchEngine:

    def __init__(self):
        self.loader = ResearchLoader()

    def run(self):

        print()
        print("========================================")
        print("ATLAS AI BACKTEST")
        print("========================================")

        df = self.loader.load()
        df = df.dropna().copy()

        print(f"Candele disponibili : {len(df)}")

        bt = Backtest(
            df,
            AtlasBacktestStrategy,
            cash=10000,
            commission=0.0002,
            exclusive_orders=True,
            finalize_trades=True,
        )

        stats = bt.run()

        print()
        print("============== REPORT ==============")
        print(f"Trades           : {stats['# Trades']}")
        print(f"Win Rate         : {stats['Win Rate [%]']:.2f}%")
        print(f"Return           : {stats['Return [%]']:.2f}%")
        print(f"Profit Factor    : {stats['Profit Factor']}")
        print(f"Drawdown         : {stats['Max. Drawdown [%]']:.2f}%")
        print(f"Equity Finale    : ${stats['Equity Final [$]']:.2f}")
        print("====================================")
        print()
        print("BACKTEST COMPLETATO.")
        print()


if __name__ == "__main__":
    ResearchEngine().run()