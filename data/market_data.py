"""
Atlas AI
Market Data
"""

import yfinance as yf


SYMBOL = "GC=F"
INTERVAL = "1h"


def load_market_data():

    df = yf.download(
        SYMBOL,
        period="2y",
        interval=INTERVAL,
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise RuntimeError(
            "Nessun dato ricevuto da Yahoo Finance."
        )

    # Gestione colonne MultiIndex di yfinance
    if hasattr(df.columns, "levels"):

        if len(df.columns.levels) > 1:

            df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # Normalizziamo i nomi
    df = df.rename(
        columns={
            "Datetime": "Datetime",
            "Date": "Datetime",
        }
    )

    required = [
        "Datetime",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Colonne mancanti: {missing}"
        )

    df = df[required].copy()

    df = df.dropna()

    df = df.sort_values("Datetime")

    df = df.drop_duplicates(
        subset=["Datetime"]
    )

    df = df.set_index("Datetime")

    return df