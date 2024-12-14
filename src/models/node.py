from __future__ import annotations

from typing import Optional, Tuple

from .allocation import AllocationGroup
from .common_names import asset_registry
from .enums import NodeType
from .hierarchy import hierarchy_manager

ROOT_NAME = "投資組合"


class Node:
    def __init__(self, name: str, node_type: NodeType) -> None:
        self.name = name
        self.node_type = node_type
        self.children: dict[str, Node] = {}
        self.allocation_group = AllocationGroup()
        self.parent_node = None

    @property
    def is_root(self) -> bool:
        return self.name == ROOT_NAME

    @property
    def full_path(self) -> str:
        path = []
        current = self
        while current.parent_node:
            path.append(current.name)
            current = current.parent_node
        return " -> ".join(reversed(path))

    @property
    def has_children(self) -> bool:
        return bool(self.children)

    @property
    def can_have_children(self) -> bool:
        return hierarchy_manager.can_have_children(self.node_type)

    def get_color(self) -> str:
        """根據節點類型返回對應的顏色"""
        color_mapping = {
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
        return color_mapping.get(self.node_type, "#7F7F7F")

    def get_available_child_names(self) -> list[str]:
        if not self.can_have_children:
            return []

        if self.is_root:
            return ["現金", "ETF", "股票", "基金", "加密貨幣", "其他"]

        available_node_types = self.get_valid_child_types()
        if not available_node_types:
            return []

        if len(available_node_types) == 1 and next(
            iter(available_node_types)
        ).name.endswith("_SYMBOL"):
            available_names = asset_registry.get_symbol_names(self.node_type)
        else:
            available_names = asset_registry.get_available_names(available_node_types)

        return available_names + ["其他"]

    def determine_child_type(self, child_name: str) -> Optional[NodeType]:
        """判斷子節點的類型"""
        valid_types = self.get_valid_child_types()
        if not valid_types:
            return None

        # 1. 如果是根節點，處理根級別的資產類型
        if self.is_root:
            root_asset_types = {
                "現金": NodeType.CASH,
                "ETF": NodeType.ETF,
                "股票": NodeType.STOCK,
                "基金": NodeType.FUND,
                "加密貨幣": NodeType.CRYPTO,
                "其他": NodeType.OTHER,
            }
            node_type = root_asset_types.get(child_name, NodeType.OTHER)
            return node_type if node_type in valid_types else None

        # 2. 處理二級節點的自定義名稱或「其他」選項
        symbol_type = NodeType.get_symbol_type(self.node_type)
        if symbol_type and symbol_type in valid_types:
            # 如果是自定義名稱或「其他」，直接返回對應的 symbol 類型
            if (
                child_name == "其他"
                or child_name not in asset_registry.get_symbol_names(self.node_type)
            ):
                return symbol_type

        # 3. 處理預定義的標的名稱
        return asset_registry.get_name_type(child_name, valid_types)

    def add_child(
        self, name: str, parent_weight: float = 100.0
    ) -> Tuple[Optional["Node"], str]:
        """添加子節點，考慮父節點權重"""
        cleaned_name = name.strip()
        if not cleaned_name or cleaned_name in self.children:
            return None, "名稱不能為空或已存在"

        if not self.can_have_children:
            return None, "不能新增子項目"

        node_type = self.determine_child_type(cleaned_name)
        if not node_type:
            return None, "不支援此項目類型"

        new_node = Node(cleaned_name, node_type)
        new_node.parent_node = self
        self.children[cleaned_name] = new_node

        self._initialize_child_allocation(cleaned_name, parent_weight)
        return new_node, ""

    def _initialize_child_allocation(self, name: str, parent_weight: float) -> None:
        """初始化子節點的配置比例"""
        if not self.allocation_group:
            self.allocation_group = AllocationGroup()

        if len(self.children) == 1:
            self.allocation_group.update_allocation(name, parent_weight)
            return

        unfixed_total = 100.0 - sum(
            self.allocation_group.allocations[n]
            for n in self.allocation_group.fixed_items
        )
        unfixed_count = len(self.children) - len(self.allocation_group.fixed_items)

        if unfixed_count > 0:
            share = unfixed_total / unfixed_count
            self.allocation_group.update_allocation(name, share)
        else:
            self.allocation_group.update_allocation(name, 0)

    def remove_child(self, name: str) -> bool:
        if name not in self.children:
            return False

        del self.children[name]
        if self.allocation_group:
            if name in self.allocation_group.allocations:
                del self.allocation_group.allocations[name]
            if name in self.allocation_group.fixed_items:
                self.allocation_group.fixed_items.remove(name)

        return True

    def get_valid_child_types(self) -> set[NodeType]:
        return hierarchy_manager.get_valid_child_types(self.node_type)
