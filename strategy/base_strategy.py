"""
Atlas AI
Base Strategy
"""


class BaseStrategy:

    name = "Base Strategy"

    def evaluate(self, df):

        raise NotImplementedError(
            "Ogni strategia deve implementare evaluate()."
        )