import inspect
from scripts.injective_market_monitor_files.alert_rule import AlertRule
import scripts.injective_market_monitor_files.alert_rules as alert_rules


class AlertRulesManager:
    def __init__(self):
        self.rules = []
        for name, obj in inspect.getmembers(alert_rules, inspect.isclass):
            if issubclass(obj, AlertRule) and obj is not AlertRule:
                self.rules.append(obj())

    def evaluate_rules_match(self, data):
        matching_rules = []
        for rule in self.rules:
            if rule.is_match(data):
                matching_rules.append(rule)
        return matching_rules
