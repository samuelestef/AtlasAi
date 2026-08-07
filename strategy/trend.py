import pandas as pd


def analyze_trend(df: pd.DataFrame):
    """
    Analizza il trend usando EMA50 ed EMA200.
    """

    last = df.iloc[-1]

    ema50 = last["EMA50"]
    ema200 = last["EMA200"]

    if ema50 > ema200:
        trend = "LONG"

    elif ema50 < ema200:
        trend = "SHORT"

    else:
        trend = "SIDEWAYS"

    distance = abs(ema50 - ema200)

    return {
        "trend": trend,
        "ema50": float(ema50),
        "ema200": float(ema200),
        "distance": float(distance)
    }