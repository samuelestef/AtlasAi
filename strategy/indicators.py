import ta


def add_indicators(df):
    """
    Aggiunge gli indicatori principali al DataFrame.
    """

    # EMA 50
    df["EMA50"] = ta.trend.ema_indicator(
        close=df["Close"],
        window=50
    )

    # EMA 200
    df["EMA200"] = ta.trend.ema_indicator(
        close=df["Close"],
        window=200
    )

    # RSI
    df["RSI"] = ta.momentum.rsi(
        close=df["Close"],
        window=14
    )

    # ATR
    df["ATR"] = ta.volatility.average_true_range(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    # ADX
    df["ADX"] = ta.trend.adx(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    # DI+
    df["DI_PLUS"] = ta.trend.adx_pos(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    # DI-
    df["DI_MINUS"] = ta.trend.adx_neg(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )

    return df