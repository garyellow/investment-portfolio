from enum import Enum, auto
from typing import Optional


class NodeType(Enum):
    ROOT = auto()  # 根節點（投資組合）
    PORTFOLIO = auto()  # 投資組合
    CASH = auto()  # 現金
    ETF = auto()  # ETF
    STOCK = auto()  # 股票
    FUND = auto()  # 基金
    CRYPTO = auto()  # 加密貨幣
    OTHER = auto()  # 其他
    # 子標的類型
    CASH_SYMBOL = auto()
    ETF_SYMBOL = auto()
    STOCK_SYMBOL = auto()
    FUND_SYMBOL = auto()
    CRYPTO_SYMBOL = auto()
    OTHER_SYMBOL = auto()

    @staticmethod
    def get_chinese_name(node_type: "NodeType") -> str:
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
        """從父節點型別推導對應的子標的型別"""
        type_mapping = {
            cls.CASH: cls.CASH_SYMBOL,
            cls.ETF: cls.ETF_SYMBOL,
            cls.STOCK: cls.STOCK_SYMBOL,
            cls.FUND: cls.FUND_SYMBOL,
            cls.CRYPTO: cls.CRYPTO_SYMBOL,
            cls.OTHER: cls.OTHER_SYMBOL,
        }
        return type_mapping.get(parent_type)


COLOR_MAP = {
    NodeType.ROOT: "#1F77B4",
    NodeType.PORTFOLIO: "#1F77B4",
    NodeType.CASH: "#2CA02C",
    NodeType.ETF: "#FF7F0E",
    NodeType.STOCK: "#D62728",
    NodeType.FUND: "#9467BD",
    NodeType.CRYPTO: "#8C564B",
    NodeType.OTHER: "#7F7F7F",
    NodeType.CASH_SYMBOL: "#2CA02C",
    NodeType.ETF_SYMBOL: "#FF7F0E",
    NodeType.STOCK_SYMBOL: "#D62728",
    NodeType.FUND_SYMBOL: "#9467BD",
    NodeType.CRYPTO_SYMBOL: "#8C564B",
    NodeType.OTHER_SYMBOL: "#7F7F7F",
}


def get_color(node_type: "NodeType") -> str:
    return COLOR_MAP.get(node_type, "#7F7F7F")
