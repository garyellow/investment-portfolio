import streamlit as st

from ..models.hierarchy import hierarchy_manager
from ..models.portfolio import PortfolioState


class AssetItemState:
    def __init__(self, portfolio_state: PortfolioState, path: list[str], name: str):
        self.portfolio_state = portfolio_state
        self.path = path
        self.name = name
        self.current = portfolio_state.get_node_by_path(path)
        self.allocation = portfolio_state.get_allocation(path, name)
        self.is_fixed = portfolio_state.is_fixed(path, name)
        self.total_items = (
            len(self.current.allocation_group.allocations) if self.current else 0
        )
        self.fixed_count = (
            len(self.current.allocation_group.fixed_items) if self.current else 0
        )
        self.unfixed_count = self.total_items - self.fixed_count if self.current else 0

    @property
    def is_single_asset(self) -> bool:
        return self.total_items == 1

    @property
    def input_disabled(self) -> bool:
        return self.is_fixed or self.is_single_asset

    @property
    def fixed_disabled(self) -> bool:
        return self.is_single_asset

    @property
    def delete_disabled(self) -> bool:
        return self.is_fixed

    @property
    def fixed_label(self) -> str:
        return "🔒" if self.is_fixed else "🔓"

    def get_fixed_help(self) -> str:
        if self.is_single_asset:
            return "單一資產無法鎖定"
        if self.is_fixed:
            all_fixed = self.fixed_count == self.total_items
            return "點擊解除鎖定" + (" (同時解除其他鎖定項目)" if all_fixed else "")
        is_last_two = self.unfixed_count == 2
        return "點擊鎖定" + (" (同時鎖定其他項目)" if is_last_two else "")

    def get_delete_help(self) -> str:
        return "已鎖定項目不可刪除" if self.is_fixed else ""


def _update_share_allocation(portfolio_state: PortfolioState, path: list[str]) -> None:
    """根據目前各項份額，計算並更新其比例配置"""
    current = portfolio_state.get_node_by_path(path)
    if not current or not current.children:
        return

    # 儲存原始的固定項目狀態及配置
    fixed_items = set(current.allocation_group.fixed_items)
    fixed_allocations = {
        name: float(current.allocation_group.get_allocation(name))
        for name in fixed_items
    }

    # 先暫時解除固定狀態
    for name in fixed_items:
        current.allocation_group.toggle_fixed(name, False)

    share_values: dict[str, float] = {}
    total_shares: float = 0.0

    # 計算非固定項目的總份額
    for name in current.children.keys():
        if name not in fixed_allocations:
            share_key = f"share_{'_'.join(path) or 'root'}_{name}"
            shares = float(st.session_state.get(share_key, 1))
            total_shares += shares
            share_values[name] = shares

    # 計算並更新配置（加入四捨五入處理）
    if total_shares > 0:
        fixed_total = sum(fixed_allocations.values())
        remaining = 100.0 - fixed_total

        # 更新非固定項目的配置，保持與 AllocationGroup 使用相同精度
        for name, shares in share_values.items():
            allocation = round((shares / total_shares) * remaining, 1)
            portfolio_state.update_allocation(path, name, allocation)

    # 恢復固定項目
    for name, allocation in fixed_allocations.items():
        portfolio_state.update_allocation(path, name, allocation)
        current.allocation_group.toggle_fixed(name, True)


def _render_asset_item(
    portfolio_state: PortfolioState, path: list[str], name: str
) -> None:
    """渲染單一資產配置項目，包括數字調整與鎖定/刪除按鈕 (百分比版)"""
    state = AssetItemState(portfolio_state, path, name)
    total_weight = portfolio_state.get_total_weight(path + [name])
    cols = st.columns([5, 1, 1])

    path_key = "_".join(path) if path else "root"
    item_key = f"{path_key}_{name}"

    locked_text = " (已鎖定)" if state.is_fixed else ""
    input_help = (
        f"局部比例：{state.allocation:.2f}%\n總體比例：{total_weight:.2f}%{locked_text}"
    )

    # 修改：使用浮點數處理百分比
    new_value = cols[0].number_input(
        label=f"**{name}** (%)",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        format="%.1f",
        value=float(state.allocation),
        disabled=state.input_disabled,
        help=input_help,
        key=f"input_{item_key}",
    )

    # 使用浮點數比較
    if abs(new_value - state.allocation) > 0.01:
        portfolio_state.update_allocation(path, name, new_value)
        st.rerun()

    cols[1].write("")
    cols[1].write("")
    if cols[1].button(
        state.fixed_label,
        key=f"fixed_{item_key}",
        help=state.get_fixed_help(),
        disabled=state.fixed_disabled,
    ):
        portfolio_state.toggle_fixed(path, name, not state.is_fixed)
        st.rerun()

    cols[2].write("")
    cols[2].write("")
    if cols[2].button(
        "🗑️",
        key=f"del_{item_key}",
        disabled=state.delete_disabled,
        help=state.get_delete_help(),
    ):
        if portfolio_state.remove_asset(path + [name]):
            st.rerun()


def _render_asset_share_item(
    portfolio_state: PortfolioState, path: list[str], name: str
) -> None:
    """渲染單一資產配置項目，包括數值調整與刪除按鈕 (份額版)"""
    state = AssetItemState(portfolio_state, path, name)
    share_key = f"share_{'_'.join(path) or 'root'}_{name}"

    default_share = int(st.session_state.get(share_key, 1))
    total_weight = portfolio_state.get_total_weight(path + [name])
    cols = st.columns([5, 1])

    input_help = f"局部比例：{state.allocation:.2f}%\n總體比例：{total_weight:.2f}%"
    new_share = cols[0].number_input(
        label=f"**{name}** (份額)",
        min_value=1,
        value=default_share,
        step=1,
        key=f"input_{share_key}",
        help=input_help,
        disabled=state.is_single_asset,
    )
    if new_share != default_share:
        st.session_state[share_key] = int(new_share)
        _update_share_allocation(portfolio_state, path)
        st.rerun()

    cols[1].write(" ")
    cols[1].write(" ")
    delete_key = f"del_share_{'_'.join(path + [name])}"
    if cols[1].button(
        "🗑️",
        key=delete_key,
        disabled=state.delete_disabled,
        help=state.get_delete_help(),
    ):
        if portfolio_state.remove_asset(path + [name]):
            st.rerun()


def render_portfolio_ui(portfolio_state: PortfolioState) -> None:
    """顯示投資組合管理介面，支援新增、刪除與資產配置"""
    with st.sidebar:
        st.title("💼 投資組合管理系統")
        st.divider()
        _render_asset_creator(portfolio_state)
        _render_asset_deleter(portfolio_state)
        with st.expander("📊 配置設定", expanded=True):
            _render_asset_allocator(portfolio_state)


def _clear_success_message() -> None:
    """清空 session 中的成功提示與上次選擇記錄"""
    st.session_state.pop("success_message", None)
    st.session_state.pop("last_selected_name", None)


def _render_asset_creator(portfolio_state: PortfolioState) -> None:
    """顯示新增資產/分類區塊"""
    with st.expander("➕ 新增資產或分類", expanded=True):
        # 過濾可新增子節點的項目
        available_nodes = [
            n for n in portfolio_state.get_all_nodes() if n.can_have_children
        ]
        location_options = ["投資組合"] + [n.full_path for n in available_nodes]

        selected_loc = st.selectbox(
            "請選擇資產所在分類", location_options, placeholder="請選擇分類"
        )
        parent_path: list[str] = selected_loc.split(" -> ")
        parent_node = portfolio_state.get_node_by_path(parent_path)

        if parent_node:
            available_names = parent_node.get_available_child_names()

            st.session_state.setdefault("last_selected_name", None)

            selected_name = st.selectbox(
                "請選擇資產", options=available_names, placeholder="請選擇資產"
            )

            if selected_name != st.session_state.last_selected_name:
                _clear_success_message()
                st.session_state.last_selected_name = selected_name

            reset_key = f"custom_name_{st.session_state.get('reset_counter', 0)}"
            new_node_name = (
                st.text_input(
                    "或輸入自訂名稱",
                    key=reset_key,
                    placeholder=(
                        "請輸入資產類型名稱"
                        if parent_node.is_root
                        else "請輸入標的名稱"
                    ),
                )
                if selected_name == "其他"
                else selected_name
            )

            if st.button(
                "確認新增資產",
                type="primary",
                use_container_width=True,
                disabled=not new_node_name,
            ):
                success, error_msg = portfolio_state.add_simplified_node(
                    parent_path, new_node_name
                )
                if success:
                    st.session_state.success_message = "新增成功！"
                    st.session_state.reset_counter = (
                        st.session_state.get("reset_counter", 0) + 1
                    )
                    st.session_state.custom_name = ""
                    st.session_state.selected_allocation_path = parent_path
                    st.rerun()
                else:
                    st.error(f"新增失敗：{error_msg}")

        if success_msg := st.session_state.pop("success_message", None):
            st.success(success_msg)


def _render_asset_deleter(portfolio_state: PortfolioState) -> None:
    """顯示刪除資產或分類的操作區塊"""
    with st.expander("🗑️ 刪除資產或分類", expanded=False):
        nodes = portfolio_state.get_all_nodes()
        if not nodes:
            st.info("目前沒有可刪除的項目")
            return
        node_options = [node.full_path for node in nodes]
        selected_node_path = st.selectbox(
            "請選擇要刪除的項目",
            options=node_options,
            key="delete_node_select",
            placeholder="請選擇項目",
        )
        if st.button("確認刪除所選項目", type="primary", use_container_width=True):
            path_list = selected_node_path.split(" -> ")
            if portfolio_state.remove_asset(path_list):
                st.success("刪除成功！")
                st.rerun()
            else:
                st.error("刪除失敗，請確認該項目是否允許刪除")


def _render_asset_allocator(portfolio_state: PortfolioState) -> None:
    """顯示資產配置設定區塊，提供百分比及份額兩種輸入模式"""
    available_nodes = [
        n for n in portfolio_state.get_all_nodes() if n.can_have_children
    ]
    node_paths = ["投資組合"] + [n.full_path for n in available_nodes]

    st.session_state.setdefault("allocation_view_path", "投資組合")
    if "selected_allocation_path" in st.session_state:
        default_path = st.session_state.selected_allocation_path
        st.session_state.allocation_view_path = (
            " -> ".join(default_path) if default_path else "投資組合"
        )
        del st.session_state.selected_allocation_path

    selected_path = st.selectbox(
        "請選擇要設定配置的分類或資產",
        node_paths,
        index=node_paths.index(st.session_state.allocation_view_path),
        placeholder="請選擇分類或資產",
    )
    st.session_state.allocation_view_path = selected_path

    allocation_mode = st.radio(
        "配置輸入模式", options=["百分比", "份額"], index=0, key="allocation_mode"
    )
    path: list[str] = selected_path.split(" -> ") if selected_path != "投資組合" else []

    if allocation_mode == "百分比":
        _render_percentage_allocation(portfolio_state, path)
    else:
        _render_share_allocation(portfolio_state, path)


def _render_percentage_allocation(
    portfolio_state: PortfolioState, path: list[str]
) -> None:
    """以百分比模式渲染資產配置"""
    if current := portfolio_state.get_node_by_path(path):
        if current.has_children:
            for name in hierarchy_manager.get_sorted_children(current):
                if name in current.children:
                    _render_asset_item(portfolio_state, path, name)


def _render_share_allocation(portfolio_state: PortfolioState, path: list[str]) -> None:
    """以份額模式渲染資產配置，立即更新各項配置"""
    if current := portfolio_state.get_node_by_path(path):
        if current.has_children:
            for name in hierarchy_manager.get_sorted_children(current):
                if name in current.children:
                    _render_asset_share_item(portfolio_state, path, name)
