import streamlit as st

from ..models.hierarchy import hierarchy_manager
from ..models.portfolio import PortfolioState


def render_portfolio_ui(portfolio_state: PortfolioState):
    with st.sidebar:
        st.title("💼 投資組合管理", anchor=False)
        st.divider()
        _render_asset_creator(portfolio_state)
        with st.expander("📊 資產配置", expanded=True):
            _render_asset_allocator(portfolio_state)


def _render_asset_creator(portfolio_state: PortfolioState) -> None:
    with st.expander("➕ 新增項目", expanded=True):
        # 過濾出只有可以包含子節點的節點路徑
        available_nodes = [
            n for n in portfolio_state.get_all_nodes() if n.can_have_children
        ]
        location_options = ["投資組合"] + [n.full_path for n in available_nodes]

        parent_path = st.selectbox(
            "位置",
            location_options,
        )
        parent_path = parent_path.split(" -> ") if parent_path != "投資組合" else []

        if parent_node := portfolio_state.get_node_by_path(parent_path):
            available_names = parent_node.get_available_child_names()  # 修正方法名稱

            # 當選擇名稱時，清除成功訊息
            if "last_selected_name" not in st.session_state:
                st.session_state.last_selected_name = None

            selected_name = st.selectbox("名稱", options=available_names)

            # 如果選擇了不同的名稱，清除成功訊息
            if selected_name != st.session_state.last_selected_name:
                if "success_message" in st.session_state:
                    del st.session_state.success_message
                st.session_state.last_selected_name = selected_name

            # 使用一個額外的 key 來控制重置
            reset_key = f"custom_name_{st.session_state.get('reset_counter', 0)}"

            if selected_name == "其他":
                placeholder = (
                    "輸入資產類型名稱" if parent_node.is_root else "輸入標的名稱"
                )
                new_node_name = st.text_input(
                    "自定義名稱", key=reset_key, placeholder=placeholder
                )
            else:
                new_node_name = selected_name

            if st.button(
                "新增",
                type="primary",
                use_container_width=True,
                disabled=not new_node_name,
            ):
                success, error_msg = portfolio_state.add_simplified_node(
                    parent_path, new_node_name
                )
                if success:
                    # 使用 session state 來保存成功訊息
                    st.session_state.success_message = "✅ 新增成功"
                    st.session_state.reset_counter = (
                        st.session_state.get("reset_counter", 0) + 1
                    )
                    st.session_state.custom_name = ""
                    st.session_state.selected_allocation_path = parent_path
                    st.rerun()
                else:
                    st.error(f"❌ {error_msg}")

        # 檢查是否有成功訊息需要顯示
        if success_msg := st.session_state.pop("success_message", None):
            st.success(success_msg)


def _render_asset_allocator(portfolio_state: PortfolioState):
    # 過濾出只有可以包含子節點的節點路徑
    available_nodes = [
        n for n in portfolio_state.get_all_nodes() if n.can_have_children
    ]
    node_paths = ["投資組合"] + [n.full_path for n in available_nodes]

    # 保存和恢復選擇的路徑
    if "allocation_view_path" not in st.session_state:
        st.session_state.allocation_view_path = "投資組合"

    # 只有在有新增項目時才更新路徑
    if "selected_allocation_path" in st.session_state:
        default_path = st.session_state.selected_allocation_path
        st.session_state.allocation_view_path = (
            " -> ".join(default_path) if default_path else "投資組合"
        )
        del st.session_state.selected_allocation_path

    selected_path = st.selectbox(
        "選擇節點",
        node_paths,
        index=node_paths.index(st.session_state.allocation_view_path),
    )
    # 更新保存的路徑
    st.session_state.allocation_view_path = selected_path

    path = selected_path.split(" -> ") if selected_path != "投資組合" else []
    _render_asset_allocator_recursive(portfolio_state, path)


def _render_asset_allocator_recursive(
    portfolio_state: PortfolioState, path: list[str]
) -> None:
    if current := portfolio_state.get_node_by_path(path):
        # 只顯示所選節點的直接子節點
        if current.has_children and current == portfolio_state.get_node_by_path(path):
            for name in hierarchy_manager.get_sorted_children(current):
                if name in current.children:
                    _render_asset_item(portfolio_state, path, name)


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
    def slider_disabled(self) -> bool:
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

    @property
    def fixed_help(self) -> str:
        if self.is_single_asset:
            return "單一資產無法固定"
        elif self.is_fixed:
            all_fixed = self.fixed_count == self.total_items
            return "點擊解除固定" + (
                " (會同時解除固定相近比例的項目)" if all_fixed else ""
            )
        else:
            is_last_two = self.unfixed_count == 2
            return "點擊固定" + (
                " (會同時固定最後兩個未固定項目)" if is_last_two else ""
            )

    @property
    def delete_help(self) -> str:
        return "無法刪除已固定項目" if self.is_fixed else None


def _render_asset_item(portfolio_state: PortfolioState, path: list[str], name: str):
    state = AssetItemState(portfolio_state, path, name)
    total_weight = portfolio_state.get_total_weight(path + [name])

    cols = st.columns([5, 1, 1])

    slider_help = (
        f"區域配置: {state.allocation:.1f}%\n"
        f"總體權重: {total_weight:.1f}%"
        + (" (已鎖定)" if state.is_fixed else "")
        + (" (唯一資產)" if state.is_single_asset else "")
    )

    new_value = cols[0].slider(
        label=f"**{name}**",
        min_value=0,
        max_value=100,
        step=5,
        value=int(round(state.allocation)),
        disabled=state.slider_disabled,
        format="%d%%",
        help=slider_help,
    )

    if abs(new_value - state.allocation) > 0.01:
        portfolio_state.update_allocation(path, name, float(new_value))
        st.rerun()

    if cols[1].button(
        state.fixed_label,
        key=f"fixed_{name}",
        help=state.fixed_help,
        disabled=state.fixed_disabled,
    ):
        portfolio_state.toggle_fixed(path, name, not state.is_fixed)
        st.rerun()

    if cols[2].button(
        "🗑️", key=f"del_{name}", disabled=state.delete_disabled, help=state.delete_help
    ):
        if portfolio_state.remove_asset(path + [name]):
            st.rerun()
