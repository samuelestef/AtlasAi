"""
Atlas AI
Risk Engine v1
"""


class RiskEngine:

    def __init__(self):

        self.account_balance = 100.0

        self.risk_percent = 1.0

        self.reward_ratio = 2.0

        self.daily_loss_limit = 2.0

        self.daily_profit_target = 3.0

    def calculate_position(self):

        risk_amount = self.account_balance * (self.risk_percent / 100)

        return round(risk_amount, 2)

    def stop_loss(self, entry_price):

        return round(entry_price - 0.0010, 5)

    def take_profit(self, entry_price):

        distance = 0.0010 * self.reward_ratio

        return round(entry_price + distance, 5)

    def report(self, entry_price):

        risk = self.calculate_position()

        sl = self.stop_loss(entry_price)

        tp = self.take_profit(entry_price)

        return {

            "risk": risk,

            "stop_loss": sl,

            "take_profit": tp

        }