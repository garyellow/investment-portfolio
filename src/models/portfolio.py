from typing import Optional, Sequence

from .enums import NodeType
from .node import Node


class PortfolioStateError(Exception):
    pass


class PortfolioState:
    def __init__(self) -> None:
        self.root = Node("投資組合", NodeType.PORTFOLIO)

    def get_node_by_path(self, path: Sequence[str]) -> Optional[Node]:
        """通過路徑獲取節點"""
        current = self.root
        for name in path:
            if name not in current.children:
                return None
            current = current.children[name]
        return current

    def remove_asset(self, path: list[str]) -> bool:
        if not path or not (current := self.get_node_by_path(path[:-1])):
            return False

        if (
            current.allocation_group
            and path[-1] in current.allocation_group.fixed_items
        ):
            return False

        if current.remove_child(path[-1]):
            if current.allocation_group and current.children:
                remaining = list(current.children.keys())
                if remaining:
                    share = 100.0 / len(remaining)
                    for name in remaining:
                        current.allocation_group.update_allocation(name, share)
            return True
        return False

    # 使用 get_node_by_path 替代原本的遍歷邏輯
    def toggle_fixed(self, path: list[str], name: str, is_locked: bool) -> None:
        if current := self.get_node_by_path(path):
            if current.allocation_group:
                current.allocation_group.toggle_fixed(name, is_locked)

    def get_allocation(self, path: list[str], name: str) -> float:
        if node := self.get_node_by_path(path):
            return node.allocation_group.allocations.get(name, 0)
        return 0

    def is_fixed(self, path: list[str], name: str) -> bool:
        if node := self.get_node_by_path(path):
            return name in node.allocation_group.fixed_items
        return False

    def get_all_nodes(self) -> list[Node]:
        def collect_nodes(current: Node) -> list[Node]:
            result = []
            for child in current.children.values():
                result.append(child)
                result.extend(collect_nodes(child))
            return result

        return collect_nodes(self.root)

    def add_simplified_node(self, path: list[str], name: str) -> tuple[bool, str]:
        """簡化版的節點添加方法，返回成功狀態和錯誤訊息"""
        if not name.strip():
            return False, "名稱不能為空"

        current = self.get_node_by_path(path)
        if not current:
            return False, "無效的路徑"

        # 計算父節點的實際權重
        parent_weight = self.get_total_weight(path)
        node, error_msg = current.add_child(name, parent_weight)
        if not node:
            return False, error_msg

        return True, ""

    def get_total_weight(self, path: list[str]) -> float:
        """計算指定路徑節點在整體投資組合中的權重"""
        if not path:
            return 100.0

        total_weight = 100.0
        current_path = []

        # 從根節點開始，逐層計算權重
        for segment in path:
            current_path.append(segment)
            parent_path = current_path[:-1]
            allocation = self.get_allocation(parent_path, segment)
            total_weight *= allocation / 100.0

        return total_weight

    def update_allocation(self, path: Sequence[str], name: str, value: float) -> None:
        """更新節點的配置比例"""
        if current := self.get_node_by_path(path):
            if current.allocation_group:
                current.allocation_group.update_allocation(name, value)
