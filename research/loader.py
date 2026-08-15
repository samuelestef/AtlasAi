"""
Atlas AI
Research Loader
"""

from data.market_data import load_market_data
from strategy.indicators import add_indicators


class ResearchLoader:

    def load(self):

        df = load_market_data()

        df = df.copy()

        df = add_indicators(df)

        return df