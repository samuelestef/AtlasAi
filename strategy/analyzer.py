"""
Atlas AI
Strategy Analyzer
"""

from research.loader import ResearchLoader


class StrategyAnalyzer:

    def run(self):

        df = ResearchLoader().load()

        df = df.dropna().copy()

        total = len(df)

        trend_ok = 0
        price_ok = 0
        rsi_ok = 0
        atr_ok = 0
        all_ok = 0

        for _, row in df.iterrows():

            trend = row["EMA50"] > row["EMA200"]

            price = row["Close"] > row["EMA50"]

            rsi = 45 <= row["RSI"] <= 65

            atr = row["ATR"] > 0.0005

            if trend:
                trend_ok += 1

            if price:
                price_ok += 1

            if rsi:
                rsi_ok += 1

            if atr:
                atr_ok += 1

            if trend and price and rsi and atr:
                all_ok += 1

        print()
        print("========================================")
        print("ATLAS STRATEGY ANALYZER")
        print("========================================")
        print()

        print(f"Candele analizzate : {total}")
        print()

        print(f"Trend LONG         : {trend_ok}")
        print(f"Prezzo > EMA50     : {price_ok}")
        print(f"RSI valido         : {rsi_ok}")
        print(f"ATR valido         : {atr_ok}")

        print()

        print(f"TUTTE LE CONDIZIONI: {all_ok}")

        print()
        print("========================================")


if __name__ == "__main__":

    StrategyAnalyzer().run()