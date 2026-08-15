"""
Atlas Strategy V1
"""

from strategy.base_strategy import BaseStrategy


class AtlasStrategyV1(BaseStrategy):

    name = "Atlas Strategy V1"

    def evaluate(self, df):

        last = df.iloc[-1]

        score = 0

        reasons = []

        if last["EMA50"] > last["EMA200"]:

            score += 30

            reasons.append("Trend LONG")

        if last["Close"] > last["EMA50"]:

            score += 20

            reasons.append("Prezzo sopra EMA50")

        if 45 <= last["RSI"] <= 65:

            score += 25

            reasons.append("RSI equilibrato")

        if last["ATR"] > 0.0005:

            score += 25

            reasons.append("ATR sufficiente")

        decision = "BUY" if score >= 80 else "NO TRADE"

        return {

            "decision": decision,

            "score": score,

            "reasons": reasons

        }