import pandas as pd
from decimal import Decimal
from tabulate import tabulate
from hummingbot.core.data_type.common import PriceType
from hummingbot.connector.connector_base import ConnectorBase, Dict
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from scripts.injective_market_monitor_files.alert_rules_manager import AlertRulesManager
from scripts.injective_market_monitor_files.slacker import Slacker


def oracle_trading_pair_mapping(trading_pair: str) -> str:
    trading_pair_map = {
        "WMATIC-USDT": "MATIC-USDT",
        "WETH-USDT": "ETH-USDT",
    }
    return trading_pair_map.get(trading_pair, trading_pair)


class MarketMonitor(ScriptStrategyBase):
    oracle_exchange = "binance_paper_trade"
    monitored_exchange = "injective_v2_paper_trade"

    MONITORING_INTERVAL = 5
    TOP_PRICE_DELTA_PCT = 2

    TRADING_PAIRS = [
        "WETH-USDT",
        "INJ-USDT",
        "ATOM-USDT",
        "TIA-USDT",
        "WMATIC-USDT",
        "SOL-USDT",
        "KAVA-USDT",
        "ARB-USDT",
    ]

    df_columns = [
        "Trading Pair",
        "Oracle Price",
        "Monitored Price",
        "% Diff",
        f"Ask Depth +{TOP_PRICE_DELTA_PCT}%",
        f"Bid Depth -{TOP_PRICE_DELTA_PCT}%",
    ]

    df_format = {
        "Trading Pair": str.upper,
        "Oracle Price": "{: ,.5f}",
        "Monitored Price": "{: ,.5f}",
        "% Diff": "{: .3%}",
        f"Ask Depth +{TOP_PRICE_DELTA_PCT}%": "{: ,.5f}",
        f"Bid Depth -{TOP_PRICE_DELTA_PCT}%": "{: ,.5f}"
    }

    markets = {
        monitored_exchange: TRADING_PAIRS,
        oracle_exchange: [oracle_trading_pair_mapping(tp) for tp in TRADING_PAIRS],
    }

    def __init__(self, connectors: Dict[str, ConnectorBase]):
        super().__init__(connectors)
        self.df = pd.DataFrame()
        self.slacker = Slacker(self.logger(), "slack_token", "testnet_market_alerts")
        self.alert_rules_mgr = AlertRulesManager()
        self.last_timestamp = 0

    def on_tick(self):
        if self.current_timestamp > self.last_timestamp + self.MONITORING_INTERVAL:
            self.last_timestamp = self.current_timestamp
            self.regenerate_df()
            anomalies = self.process_anomalies()
            if anomalies:
                for trading_pair, messages in anomalies.items():
                    self.logger().info(f"{trading_pair}: {' | '.join(messages)}")
                    # self.slacker.send_message(f"Anomalies detected for {trading_pair}: {messages}")

    def regenerate_df(self):
        rows = []
        for trading_pair in self.TRADING_PAIRS:
            oracle_trading_pair = oracle_trading_pair_mapping(trading_pair)
            oracle_price = self.connectors[self.oracle_exchange].get_price_by_type(oracle_trading_pair,
                                                                                   PriceType.MidPrice)
            monitored_price = self.connectors[self.monitored_exchange].get_price_by_type(trading_pair,
                                                                                         PriceType.MidPrice)
            _top_ask_price = monitored_price * Decimal(1 + (self.TOP_PRICE_DELTA_PCT / 100))
            _top_bid_price = monitored_price * Decimal(1 - (self.TOP_PRICE_DELTA_PCT / 100))

            _ask_depth_in_base = self.connectors[self.monitored_exchange].get_volume_for_price(trading_pair,
                                                                                               True,
                                                                                               _top_ask_price).result_volume
            _bid_depth_in_base = self.connectors[self.monitored_exchange].get_volume_for_price(trading_pair,
                                                                                               False,
                                                                                               _top_bid_price).result_volume
            _ask_depth_vwap = self.connectors[self.monitored_exchange].get_vwap_for_volume(trading_pair,
                                                                                           True,
                                                                                           _ask_depth_in_base).result_price
            _bid_depth_vwap = self.connectors[self.monitored_exchange].get_vwap_for_volume(trading_pair,
                                                                                           False,
                                                                                           _bid_depth_in_base).result_price
            ask_depth_in_quote = _ask_depth_in_base * _ask_depth_vwap
            bid_depth_in_quote = _bid_depth_in_base * _bid_depth_vwap
            difference = (monitored_price - oracle_price) / oracle_price * 100
            rows.append(
                (trading_pair, oracle_price, monitored_price, difference, ask_depth_in_quote, bid_depth_in_quote))
        self.df = pd.DataFrame(rows, columns=self.df_columns)

    def process_anomalies(self):
        results = {}
        for _, row in self.df.iterrows():
            matching_rules = self.alert_rules_mgr.evaluate_rules_match(row)
            if matching_rules:
                results[row["Trading Pair"]] = [rule.prompt(row) for rule in matching_rules]
        return results

    def on_stop(self):
        pass

    def format_status(self) -> str:
        formatted_df = self.df.style.format(self.df_format).data
        return tabulate(formatted_df, headers="keys", colalign="center", tablefmt="grid")
