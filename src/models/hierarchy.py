from .enums import NodeType


class HierarchyManager:
    def __init__(self):
        self._hierarchy = {
            NodeType.PORTFOLIO: {
                NodeType.CASH,
                NodeType.ETF,
                NodeType.STOCK,
                NodeType.FUND,
                NodeType.CRYPTO,
                NodeType.OTHER,
            },
            NodeType.CASH: {NodeType.CASH_SYMBOL},
            NodeType.ETF: {NodeType.ETF_SYMBOL},
            NodeType.STOCK: {NodeType.STOCK_SYMBOL},
            NodeType.FUND: {NodeType.FUND_SYMBOL},
            NodeType.CRYPTO: {NodeType.CRYPTO_SYMBOL},
            NodeType.OTHER: {NodeType.OTHER_SYMBOL},
        }

        self._terminal_types = {
            NodeType.CASH_SYMBOL,
            NodeType.ETF_SYMBOL,
            NodeType.STOCK_SYMBOL,
            NodeType.FUND_SYMBOL,
            NodeType.CRYPTO_SYMBOL,
            NodeType.OTHER_SYMBOL,
        }

        self._root_order = [
            NodeType.CASH,
            NodeType.ETF,
            NodeType.STOCK,
            NodeType.FUND,
            NodeType.CRYPTO,
            NodeType.OTHER,
        ]

    def get_valid_child_types(self, node_type: NodeType) -> set[NodeType]:
        return self._hierarchy.get(node_type, set())

    def can_have_children(self, node_type: NodeType) -> bool:
        return node_type not in self._terminal_types

    def get_root_order(self) -> list[str]:
        return [NodeType.get_chinese_name(t) for t in self._root_order]

    def get_sorted_children(self, node) -> list[str]:
        if node.is_root:
            standard_names = self.get_root_order()
            custom_names = [
                name for name in node.children.keys() if name not in standard_names
            ]
            return standard_names + sorted(custom_names)
        return sorted(node.children.keys())


hierarchy_manager = HierarchyManager()
