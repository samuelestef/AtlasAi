"""
Atlas AI
Strategy V2
"""

class AtlasStrategyV2:

    name = "Atlas Strategy V2"

    def evaluate(self, df):

        row = df.iloc[-1]

        reasons = []

        score = 0

        trend = row["EMA50"] > row["EMA200"]

        if trend:
            score += 25
            reasons.append("Trend LONG")

        price = row["Close"] > row["EMA50"]

        if price:
            score += 20
            reasons.append("Prezzo sopra EMA50")

        rsi = 50 <= row["RSI"] <= 60

        if rsi:
            score += 20
            reasons.append("RSI ottimale")

        atr = row["ATR"] > 0.0005

        if atr:
            score += 15
            reasons.append("Volatilità sufficiente")

        highest10 = df["High"].tail(10).max()

        breakout = row["Close"] >= highest10

        if breakout:
            score += 20
            reasons.append("Breakout ultime 10 candele")

        if score >= 80:
            decision = "BUY"

        elif score >= 60:
            decision = "WATCH"

        else:
            decision = "NO TRADE"

        return {
            "decision": decision,
            "score": score,
            "reasons": reasons,
        }