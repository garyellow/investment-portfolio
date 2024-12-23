import io
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd
import requests

from .enums import NodeType
from .utils.fetcher import fetch_json


class AssetDataProvider(ABC):
    @abstractmethod
    def get_symbols(self) -> list[str]:
        """Get asset symbols for the specific asset type."""
        pass


class CashSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        data = fetch_json("https://openexchangerates.org/api/currencies.json")
        if data is None:
            return [
                "(USD) US Dollar",
                "(TWD) New Taiwan Dollar",
                "(JPY) Japanese Yen",
                "(CNY) Chinese Yuan",
            ]
        cash_symbols = set()
        for symbol, name in data.items():
            if len(symbol) == 3:
                formatted_symbol = f"({symbol}) {name}"
                cash_symbols.add(formatted_symbol)
        return sorted(list(cash_symbols))


class ETFSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        data = fetch_json("https://openapi.tdcc.com.tw/v1/opendata/2-41")
        if data is None:
            return ["(0050) 元大台灣50"]
        etf_symbols = set()
        for item in data:
            if "證券代號" in item and "證券名稱" in item:
                formatted_symbol = f"({item['證券代號'].rstrip()}) {item['證券名稱']}"
                etf_symbols.add(formatted_symbol)
        return sorted(list(etf_symbols))


class StockSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        stock_symbols = set()
        tpex_data = fetch_json(
            "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis",
            headers={
                "accept": "application/json",
                "If-Modified-Since": "Mon, 26 Jul 1997 05:00:00 GMT",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        if tpex_data:
            for item in tpex_data:
                if "SecuritiesCompanyCode" in item and "CompanyName" in item:
                    formatted_symbol = (
                        f"({item['SecuritiesCompanyCode']}) {item['CompanyName']}"
                    )
                    stock_symbols.add(formatted_symbol)
        twse_data = fetch_json(
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            headers={
                "accept": "application/json",
                "If-Modified-Since": "Mon, 26 Jul 1997 05:00:00 GMT",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        if twse_data:
            for item in twse_data:
                if "公司代號" in item and "公司簡稱" in item:
                    formatted_symbol = f"({item['公司代號']}) {item['公司簡稱']}"
                    stock_symbols.add(formatted_symbol)
        if stock_symbols:
            return sorted(list(stock_symbols))
        return ["(2330) TSMC"]


class FundSymbolProvider(AssetDataProvider):
    def _fetch_excel_names(self, url: str) -> set[str]:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content))
        return set(df["基金名稱"].dropna().unique())

    def get_symbols(self) -> list[str]:
        try:
            fund_names = set()
            domestic_url = (
                "https://www.sitca.org.tw/MemberK0000/R/01/境內基金代碼對照表.xlsx"
            )
            fund_names.update(self._fetch_excel_names(domestic_url))
            foreign_url = (
                "https://www.sitca.org.tw/MemberK0000/R/02/境外基金代碼對照表.xlsx"
            )
            fund_names.update(self._fetch_excel_names(foreign_url))
            return sorted(list(fund_names))
        except Exception as e:
            print(f"Error fetching fund symbols: {e}")
            return ["富邦台灣科技", "元大高科技", "國泰科技"]


class CryptoSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        data = fetch_json(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 50,
                "page": 1
            },
        )
        if data is None:
            return ["(BTC) Bitcoin", "(ETH) Ethereum", "(USDT) Tether"]
        crypto_symbols = set()
        for coin in data:
            if "symbol" in coin and "name" in coin:
                formatted_symbol = f"({coin['symbol'].upper()}) {coin['name']}"
                crypto_symbols.add(formatted_symbol)
        return sorted(list(crypto_symbols))


class OtherSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        return []


class AssetDataProviderFactory:
    @staticmethod
    def create_provider(node_type: NodeType) -> AssetDataProvider:
        if node_type == NodeType.CASH_SYMBOL:
            return CashSymbolProvider()
        elif node_type == NodeType.ETF_SYMBOL:
            return ETFSymbolProvider()
        elif node_type == NodeType.STOCK_SYMBOL:
            return StockSymbolProvider()
        elif node_type == NodeType.FUND_SYMBOL:
            return FundSymbolProvider()
        elif node_type == NodeType.CRYPTO_SYMBOL:
            return CryptoSymbolProvider()
        elif node_type == NodeType.OTHER_SYMBOL:
            return OtherSymbolProvider()
        else:
            raise ValueError(f"Unsupported node type: {node_type}")


class AssetNameRegistry:
    def __init__(self):
        self._asset_type_map: dict[str, set[NodeType]] = {}
        symbol_types = {
            NodeType.CASH_SYMBOL,
            NodeType.ETF_SYMBOL,
            NodeType.STOCK_SYMBOL,
            NodeType.FUND_SYMBOL,
            NodeType.CRYPTO_SYMBOL,
            NodeType.OTHER_SYMBOL,
        }
        for node_type in NodeType:
            if node_type in symbol_types:
                provider = AssetDataProviderFactory.create_provider(node_type)
                symbols = provider.get_symbols()
                for symbol in symbols:
                    if symbol not in self._asset_type_map:
                        self._asset_type_map[symbol] = set()
                    self._asset_type_map[symbol].add(node_type)

    def get_available_names(self, available_types: set[NodeType]) -> list[str]:
        available_names = {
            name
            for name, types in self._asset_type_map.items()
            if types & available_types
        }
        return sorted(available_names)

    def get_name_type(
        self, name: str, valid_types: set[NodeType]
    ) -> Optional[NodeType]:
        if name in self._asset_type_map:
            matching_types = self._asset_type_map[name] & valid_types
            return next(iter(matching_types)) if matching_types else None
        return None

    def get_symbol_names(self, parent_type: NodeType) -> list[str]:
        if symbol_type := NodeType.get_symbol_type(parent_type):
            names = {
                name
                for name, types in self._asset_type_map.items()
                if symbol_type in types
            }
            return sorted(names)
        return []


asset_registry = AssetNameRegistry()
