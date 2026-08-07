from loguru import logger

from data.market_data import load_market_data
from strategy.indicators import add_indicators
from strategy.trend import analyze_trend


def main():

    logger.info("Download dati...")

    df = load_market_data()

    logger.info("Calcolo indicatori...")

    df = add_indicators(df)

    trend = analyze_trend(df)

    print()
    print("======== TREND ENGINE ========")

    print(f"Trend: {trend['trend']}")
    print(f"EMA50 : {trend['ema50']:.5f}")
    print(f"EMA200: {trend['ema200']:.5f}")
    print(f"Distanza EMA: {trend['distance']:.5f}")


if __name__ == "__main__":
    main()