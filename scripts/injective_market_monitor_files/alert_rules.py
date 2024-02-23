from scripts.injective_market_monitor_files.alert_rule import AlertRule


class AskLiquidityIsTooLow(AlertRule):
    MIN_LIQUIDITY = 1000

    def is_match(self, data):
        return data["Ask Depth +2%"] < self.MIN_LIQUIDITY

    def prompt(self, data):
        return f"Ask liquidity={data['Ask Depth +2%']} is below {self.MIN_LIQUIDITY}!"


class BidLiquidityIsTooLow(AlertRule):
    MIN_LIQUIDITY = 1000

    def is_match(self, data):
        return data["Bid Depth -2%"] < self.MIN_LIQUIDITY

    def prompt(self, data):
        return f"Bid liquidity={data['Bid Depth -2%']} is below {self.MIN_LIQUIDITY}!"


class PriceDifferenceIsTooBig(AlertRule):
    MAX_DIFFERENCE = 0.5

    def is_match(self, data):
        return abs(data["% Diff"]) > self.MAX_DIFFERENCE

    def prompt(self, data):
        return f"Price difference={'{: .3}'.format(float(data['% Diff']))}% abs value is above {self.MAX_DIFFERENCE}%!"
