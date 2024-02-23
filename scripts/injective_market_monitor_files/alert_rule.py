from abc import ABC, abstractmethod


class AlertRule(ABC):
    @abstractmethod
    def is_match(self, data):
        """
        Evaluates the rule against the provided data.

        Parameters:
        data: The input data to be evaluated by the rule.

        Returns:
        bool: True if the data matches the rule's condition, False otherwise.
        """
        pass

    @abstractmethod
    def prompt(self, data):
        """
        Returns prompt that matches criteria which triggered the alert.
        """
        pass
