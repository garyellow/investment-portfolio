from abc import ABC, abstractmethod
from typing import Optional
import requests

from .enums import NodeType


class AssetDataProvider(ABC):
    @abstractmethod
    def get_symbols(self) -> list[str]:
        """Get asset symbols for the specific asset type."""
        pass


class CashSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        # TODO: 實作從 API 獲取現金符號的邏輯
        return ["USD", "TWD", "JPY", "CNY"]


class ETFSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        try:
            url = "https://openapi.tdcc.com.tw/v1/opendata/2-41"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            # Create formatted strings with code and name
            etf_symbols = set()
            for item in data:
                if "證券代號" in item and "證券名稱" in item:
                    formatted_symbol = (
                        f"({item['證券代號'].rstrip()}) {item['證券名稱']}"
                    )
                    etf_symbols.add(formatted_symbol)

            return sorted(list(etf_symbols))
        except Exception as e:
            print(f"Error fetching ETF symbols: {e}")
            # Fallback to default symbols if API call fails
            return ["(0050) 元大台灣50"]


class StockSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        stock_symbols = set()
        
        # Fetch from TPEX API
        try:
            tpex_url = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"
            headers = {
                'accept': 'application/json',
                'If-Modified-Since': 'Mon, 26 Jul 1997 05:00:00 GMT',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            tpex_response = requests.get(tpex_url, headers=headers)
            tpex_response.raise_for_status()

            tpex_data = tpex_response.json()
            for item in tpex_data:
                if "SecuritiesCompanyCode" in item and "CompanyName" in item:
                    formatted_symbol = (
                        f"({item['SecuritiesCompanyCode']}) {item['CompanyName']}"
                    )
                    stock_symbols.add(formatted_symbol)
        except Exception as e:
            print(f"Error fetching TPEX symbols: {e}")

        # Fetch from TWSE API
        try:
            twse_url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
            twse_response = requests.get(twse_url, headers=headers)
            twse_response.raise_for_status()

            twse_data = twse_response.json()
            for item in twse_data:
                if "公司代號" in item and "公司簡稱" in item:
                    formatted_symbol = (
                        f"({item['公司代號']}) {item['公司簡稱']}"
                    )
                    stock_symbols.add(formatted_symbol)
        except Exception as e:
            print(f"Error fetching TWSE symbols: {e}")

        # Return combined results or fallback to default if both APIs fail
        if stock_symbols:
            return sorted(list(stock_symbols))
        return ["(2330) TSMC"]  # Fallback value if both APIs fail


class FundSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        # TODO: 實作從 API 獲取基金符號的邏輯
        return ["富邦台灣科技", "元大高科技", "國泰科技"]


class CryptoSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        # TODO: 實作從 API 獲取加密貨幣符號的邏輯
        return ["BTC", "ETH", "USDT"]


class OtherSymbolProvider(AssetDataProvider):
    def get_symbols(self) -> list[str]:
        # TODO: 實作從 API 獲取其他符號的邏輯
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

        # 只處理 symbol 類型的節點
        symbol_types = {
            NodeType.CASH_SYMBOL,
            NodeType.ETF_SYMBOL,
            NodeType.STOCK_SYMBOL,
            NodeType.FUND_SYMBOL,
            NodeType.CRYPTO_SYMBOL,
            NodeType.OTHER_SYMBOL,
        }

        for node_type in NodeType:
            if node_type in symbol_types:  # 只為 symbol 類型創建 provider
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
