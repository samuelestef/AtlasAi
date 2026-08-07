import yfinance as yf
import pandas as pd

SYMBOL = "EURUSD=X"


def load_market_data(period="60d", interval="1h"):
    df = yf.download(
        SYMBOL,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False
    )

    # Se Yahoo restituisce colonne MultiIndex le rendiamo semplici
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    return df


if __name__ == "__main__":
    data = load_market_data()
    print(data.head())
    print()
    print(f"Candele scaricate: {len(data)}")