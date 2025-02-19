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
        for name in path[1:]:
            if name not in current.children:
                return None

            current = current.children[name]

        return current

    def remove_asset(self, path: list[str]) -> bool:
        """依路徑移除資產，成功返回 True"""
        if not path or not (current := self.get_node_by_path(path[:-1])):
            return False
        if current.allocation_group and path[-1] in current.allocation_group.fixed_items:
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
        """遞迴收集所有子節點"""
        def collect_nodes(current: Node) -> list[Node]:
            result = []
            for child in current.children.values():
                result.append(child)
                result.extend(collect_nodes(child))
            return result
        return collect_nodes(self.root)

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
        """計算節點於整體組合中的權重"""
        total_weight = 100.0
        for i, segment in enumerate(path):
            # 透過區間前一段作為父路徑
            allocation = self.get_allocation(path[:i], segment)
            total_weight *= allocation / 100.0
        return total_weight

    def update_allocation(self, path: list[str], name: str, value: float) -> None:
        """更新指定節點的配置比例"""
        if current := self.get_node_by_path(path):
            if current.allocation_group:
                current.allocation_group.update_allocation(name, value)
