from enum import Enum, auto
from typing import Optional


class NodeType(Enum):
    ROOT = auto()  # 根節點（投資組合）
    PORTFOLIO = auto()
    CASH = auto()
    ETF = auto()
    STOCK = auto()
    FUND = auto()
    CRYPTO = auto()
    OTHER = auto()

    # 子標的類型
    CASH_SYMBOL = auto()
    ETF_SYMBOL = auto()
    STOCK_SYMBOL = auto()
    FUND_SYMBOL = auto()
    CRYPTO_SYMBOL = auto()
    OTHER_SYMBOL = auto()

    @staticmethod
    def get_chinese_name(node_type) -> str:
        name_map = {
            NodeType.PORTFOLIO: "投資組合",
            NodeType.CASH: "現金",
            NodeType.ETF: "ETF",
            NodeType.STOCK: "股票",
            NodeType.FUND: "基金",
            NodeType.CRYPTO: "加密貨幣",
            NodeType.OTHER: "其他",
            NodeType.CASH_SYMBOL: "現金標的",
            NodeType.ETF_SYMBOL: "ETF標的",
            NodeType.STOCK_SYMBOL: "股票標的",
            NodeType.FUND_SYMBOL: "基金標的",
            NodeType.CRYPTO_SYMBOL: "加密貨幣標的",
            NodeType.OTHER_SYMBOL: "其他標的",
        }
        return name_map.get(node_type, "未知類型")

    @classmethod
    def get_symbol_type(cls, parent_type: "NodeType") -> Optional["NodeType"]:
        """根據父節點類型取得對應的子標的類型"""
        type_mapping = {
            cls.CASH: cls.CASH_SYMBOL,
            cls.ETF: cls.ETF_SYMBOL,
            cls.STOCK: cls.STOCK_SYMBOL,
            cls.FUND: cls.FUND_SYMBOL,
            cls.CRYPTO: cls.CRYPTO_SYMBOL,
            cls.OTHER: cls.OTHER_SYMBOL,
        }
        return type_mapping.get(parent_type)
