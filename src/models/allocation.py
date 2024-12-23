from decimal import ROUND_HALF_UP, Decimal
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
        """取得指定名稱的百分比值，如果不存在則返回預設值"""
        return self.allocations.get(name, default)

    def update_allocation(self, name: str, value: float) -> None:
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

        unlocked = [
            k for k in self.allocations if k not in self.fixed_items and k != name
        ]

        old_value = self.allocations[name]
        self.allocations[name] = value

        if abs(old_value - value) > 0.01:
            remaining = available - value
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
        total_percentage = Decimal("0")
        unlocked_items = [k for k in self.allocations if k not in self.fixed_items]

        for name, value in self.allocations.items():
            total_percentage += Decimal(str(value))

        if abs(total_percentage - Decimal("100")) > Decimal("0.1"):
            unlocked_sum = sum(
                Decimal(str(self.allocations[k])) for k in unlocked_items
            )
            if unlocked_sum > 0:
                adjustment_ratio = (
                    Decimal("100")
                    - sum(Decimal(str(self.allocations[k])) for k in self.fixed_items)
                ) / unlocked_sum

                for name in unlocked_items:
                    value = Decimal(str(self.allocations[name])) * adjustment_ratio
                    self.allocations[name] = float(
                        value.quantize(Decimal("0.1"), ROUND_HALF_UP)
                    )

    def has_single_unlocked_item(self) -> bool:
        """檢查是否只有一個未鎖定的項目"""
        return len(self.allocations) - len(self.fixed_items) == 1

    def toggle_fixed(self, name: str, is_fixed: bool) -> None:
        if name not in self.allocations:
            return

        if is_fixed:
            if (
                sum(self.allocations.get(n, 0) for n in self.fixed_items)
                + self.allocations[name]
                > 99.9
            ):
                return

            unlocked_items = [k for k in self.allocations if k not in self.fixed_items]
            if len(unlocked_items) == 2 and name in unlocked_items:
                other_item = next(k for k in unlocked_items if k != name)
                self.fixed_items.update([name, other_item])
                return

            self.fixed_items.add(name)
            self._redistribute_allocations()
        else:
            if name in self.fixed_items:
                if (
                    len(self.fixed_items) == len(self.allocations)
                    and len(self.allocations) > 1
                ):
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
        total_locked_percentage = sum(
            self.allocations.get(name, 0) for name in self.fixed_items
        )
        available_percentage = 100 - total_locked_percentage
        unlocked_item_names = [k for k in self.allocations if k not in self.fixed_items]

        if not unlocked_item_names:
            return

        total_unlocked_percentage = sum(
            self.allocations[k] for k in unlocked_item_names
        )

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
