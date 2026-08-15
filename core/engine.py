"""
Atlas AI
Core Engine
"""

from loguru import logger

from data.market_data import load_market_data
from strategy.indicators import add_indicators
from strategy.trend import analyze_trend
from strategy.atlas_strategy_v1 import AtlasStrategyV1
from risk.risk_engine import RiskEngine


class Engine:

    def run(self):

        logger.info("Atlas AI Engine avviato")

        # Caricamento dati
        df = load_market_data()

        # Indicatori
        df = add_indicators(df)

        # Trend
        trend = analyze_trend(df)

        # Strategia
        strategy = AtlasStrategyV1()

        result = strategy.evaluate(df)

        # Gestione rischio
        price = float(df.iloc[-1]["Close"])

        risk = RiskEngine().report(price)

        # Output
        print()

        print("========================================")
        print("ATLAS AI")
        print("========================================")

        print(f"Strategia : {strategy.name}")
        print(f"Trend     : {trend['trend']}")
        print(f"Decisione : {result['decision']}")
        print(f"Score     : {result['score']}/100")

        print()

        print(f"Prezzo     : {price:.5f}")
        print(f"Stop Loss  : {risk['stop_loss']}")
        print(f"Take Profit: {risk['take_profit']}")
        print(f"Rischio €  : {risk['risk']}")

        print()

        print("Motivi")

        for reason in result["reasons"]:
            print(f"✓ {reason}")

        print()
        print("========================================")