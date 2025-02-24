from typing import Optional

from .enums import NodeType
from .node import Node


class PortfolioStateError(Exception):
    pass


class PortfolioState:
    def __init__(self) -> None:
        # 建立根節點
        self.root = Node("投資組合", NodeType.PORTFOLIO)

    def get_node_by_path(self, path: list[str]) -> Optional[Node]:
        """根據路徑逐層查找節點，找不到返回 None"""
        current = self.root
        remaining = path[1:] if path and path[0] == current.name else path
        for name in remaining:
            if name not in current.children:
                return None
            current = current.children[name]
        return current

    def remove_asset(self, path: list[str]) -> bool:
        if not path:
            return False
        parent = self.get_node_by_path(path[:-1])
        if not parent or (
            parent.allocation_group and path[-1] in parent.allocation_group.fixed_items
        ):
            return False
        if parent.remove_child(path[-1]):
            if parent.allocation_group and parent.children:
                remaining = list(parent.children.keys())
                share = 100.0 / len(remaining)
                for n in remaining:
                    parent.allocation_group.update_allocation(n, share)
            return True
        return False

    def toggle_fixed(self, path: list[str], name: str, is_locked: bool) -> None:
        """切換指定資產的鎖定狀態"""
        if current := self.get_node_by_path(path):
            if current.allocation_group:
                current.allocation_group.toggle_fixed(name, is_locked)

    def get_allocation(self, path: list[str], name: str) -> float:
        """取得指定資產的配置比例"""
        if node := self.get_node_by_path(path):
            return node.allocation_group.allocations.get(name, 0)
        return 0

    def is_fixed(self, path: list[str], name: str) -> bool:
        """檢查指定資產是否已鎖定"""
        if node := self.get_node_by_path(path):
            return name in node.allocation_group.fixed_items
        return False

    def get_all_nodes(self) -> list[Node]:
        def collect(node: Node) -> list[Node]:
            return list(node.children.values()) + [
                child for n in node.children.values() for child in collect(n)
            ]

        return collect(self.root)

    def add_simplified_node(self, path: list[str], name: str) -> tuple[bool, str]:
        """
        新增節點，返回 (是否成功, 錯誤訊息)。
        名稱空或重複時返回錯誤。
        """
        if not name.strip():
            return False, "名稱不能為空"
        current = self.get_node_by_path(path)
        if not current:
            return False, "無效的路徑"
        parent_weight = self.get_total_weight(path)
        child_node, error_msg = current.add_child(name, parent_weight)
        if not child_node:
            return False, error_msg
        return True, ""

    def get_total_weight(self, path: list[str]) -> float:
        if path and path[0] == self.root.name:
            path = path[1:]

        total = 100.0
        current = self.root
        for name in path:
            # 若目前層級未設定 allocation，則使用平均比例分配
            allocation = current.allocation_group.allocations.get(name)
            if allocation is None or allocation == 0:
                children_count = len(current.children)
                allocation = 100.0 / children_count if children_count else 0.0
            total = total * allocation / 100.0
            next_node = current.children.get(name)
            if next_node is None:
                break
            current = next_node
        return total

    def update_allocation(self, path: list[str], name: str, value: float) -> None:
        """更新指定節點的配置比例"""
        if current := self.get_node_by_path(path):
            if current.allocation_group:
                current.allocation_group.update_allocation(name, value)
