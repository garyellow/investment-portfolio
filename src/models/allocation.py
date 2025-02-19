from typing import AbstractSet, Mapping


class AllocationGroup:
    def __init__(self) -> None:
        self.allocations: dict[str, float] = {}
        self.fixed_items: set[str] = set()

    def get_allocations(self) -> Mapping[str, float]:
        return self.allocations.copy()

    def get_fixed_items(self) -> AbstractSet[str]:
        return frozenset(self.fixed_items)

    def get_allocation(self, name: str, default: float = 0.0) -> float:
        """取得指定項目的百分比，若不存在則返回預設值"""
        return self.allocations.get(name, default)

    def update_allocation(self, name: str, value: float) -> None:
        """更新指定項目的配置比例，並自動重新分配其他項目比例"""
        if name in self.fixed_items:
            return

        if not self.allocations:
            self.allocations[name] = 100.0
            return

        if name not in self.allocations:
            self.allocations[name] = 0.0

        locked_sum = sum(self.allocations.get(n, 0) for n in self.fixed_items)
        available = 100 - locked_sum

        value = min(max(0.0, value), available)
        old_value = self.allocations[name]
        self.allocations[name] = value

        if abs(old_value - value) > 0.01:
            remaining = available - value
            unlocked = [k for k in self.allocations if k not in self.fixed_items and k != name]
            if unlocked:
                others_total = sum(self.allocations.get(k, 0) for k in unlocked)
                if others_total > 0:
                    ratio = remaining / others_total
                    for k in unlocked:
                        self.allocations[k] = self.allocations.get(k, 0) * ratio
                else:
                    equal_share = remaining / len(unlocked)
                    for k in unlocked:
                        self.allocations[k] = equal_share
            self._normalize()

    def _normalize(self) -> None:
        """正規化所有項目的總和為 100%"""
        total_percentage = sum(self.allocations.values())
        if abs(total_percentage - 100) > 0.1:
            unlocked_items = [k for k in self.allocations if k not in self.fixed_items]
            locked_total = sum(self.allocations.get(k, 0) for k in self.fixed_items)
            if unlocked_items:
                for name in unlocked_items:
                    self.allocations[name] = round(
                        self.allocations[name] / total_percentage * (100 - locked_total), 1
                    )

    def has_single_unlocked_item(self) -> bool:
        """檢查是否只有一個未鎖定項目"""
        return len(self.allocations) - len(self.fixed_items) == 1

    def toggle_fixed(self, name: str, is_fixed: bool) -> None:
        """
        設定或取消指定項目的鎖定狀態，
        並根據狀態調整其他項目的比例。
        """
        if name not in self.allocations:
            return

        if is_fixed:
            current_locked = sum(self.allocations.get(n, 0) for n in self.fixed_items)
            if current_locked + self.allocations[name] > 99.9:
                return

            unlocked_items = [k for k in self.allocations if k not in self.fixed_items]
            if len(unlocked_items) == 2 and name in unlocked_items:
                self.fixed_items.update([name] + [k for k in unlocked_items if k != name])
                return

            self.fixed_items.add(name)
            self._redistribute_allocations()
        else:
            if name in self.fixed_items:
                if len(self.fixed_items) == len(self.allocations) and len(self.allocations) > 1:
                    closest_item = min(
                        (k for k in self.fixed_items if k != name),
                        key=lambda k: abs(self.allocations[k] - self.allocations[name]),
                        default=None,
                    )
                    if closest_item:
                        self.fixed_items.remove(closest_item)
                self.fixed_items.remove(name)
                self._normalize()

    def _redistribute_allocations(self) -> None:
        """重新分配未鎖定項目的百分比以滿足總和 100%"""
        total_locked_percentage = sum(self.allocations.get(name, 0) for name in self.fixed_items)
        available_percentage = 100 - total_locked_percentage
        unlocked_item_names = [k for k in self.allocations if k not in self.fixed_items]

        if not unlocked_item_names:
            return

        total_unlocked_percentage = sum(self.allocations[k] for k in unlocked_item_names)

        if total_unlocked_percentage > 0:
            percentage_ratio = available_percentage / total_unlocked_percentage
            for item_name in unlocked_item_names:
                self.allocations[item_name] = round(
                    self.allocations[item_name] * percentage_ratio, 1
                )
        else:
            equal_percentage = round(available_percentage / len(unlocked_item_names), 1)
            for item_name in unlocked_item_names:
                self.allocations[item_name] = equal_percentage

        self._normalize()
