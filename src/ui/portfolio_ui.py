import streamlit as st
from ..models.hierarchy import hierarchy_manager
from ..models.portfolio import PortfolioState

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
        available_nodes = [n for n in portfolio_state.get_all_nodes() if n.can_have_children]
        location_options = ["投資組合"] + [n.full_path for n in available_nodes]

        selected_loc = st.selectbox("請選擇資產所在分類", location_options)
        parent_path: list[str] = selected_loc.split(" -> ")
        parent_node = portfolio_state.get_node_by_path(parent_path)

        if parent_node:
            available_names = parent_node.get_available_child_names()

            st.session_state.setdefault("last_selected_name", None)

            selected_name = st.selectbox("請選擇預設名稱", options=available_names)

            if selected_name != st.session_state.last_selected_name:
                _clear_success_message()
                st.session_state.last_selected_name = selected_name

            reset_key = f"custom_name_{st.session_state.get('reset_counter', 0)}"
            new_node_name = (
                st.text_input("或輸入自訂名稱", key=reset_key,
                              placeholder=("請輸入資產類型名稱" if parent_node.is_root else "請輸入標的名稱"))
                if selected_name == "其他" else selected_name
            )

            if st.button("確認新增資產", type="primary", use_container_width=True, disabled=not new_node_name):
                success, error_msg = portfolio_state.add_simplified_node(parent_path, new_node_name)
                if success:
                    st.session_state.success_message = "新增成功！"
                    st.session_state.reset_counter = st.session_state.get("reset_counter", 0) + 1
                    st.session_state.custom_name = ""
                    st.session_state.selected_allocation_path = parent_path
                    st.rerun()
                else:
                    st.error(f"新增失敗：{error_msg}")

        if (success_msg := st.session_state.pop("success_message", None)):
            st.success(success_msg)

def _render_asset_deleter(portfolio_state: PortfolioState) -> None:
    """顯示刪除資產或分類的操作區塊"""
    with st.expander("🗑️ 刪除資產或分類", expanded=False):
        nodes = portfolio_state.get_all_nodes()  # 取得所有非根節點
        if not nodes:
            st.info("目前沒有可刪除的項目")
            return
        node_options = [node.full_path for node in nodes]
        selected_node_path = st.selectbox("請選擇要刪除的項目", options=node_options, key="delete_node_select")
        if st.button("確認刪除所選項目", type="primary", use_container_width=True):
            path_list = selected_node_path.split(" -> ")
            if portfolio_state.remove_asset(path_list):
                st.success("刪除成功！")
                st.rerun()
            else:
                st.error("刪除失敗，請確認該項目是否允許刪除")

def _render_asset_allocator(portfolio_state: PortfolioState) -> None:
    """顯示資產配置設定區塊，提供百分比及份額兩種輸入模式"""
    available_nodes = [n for n in portfolio_state.get_all_nodes() if n.can_have_children]
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
    )
    st.session_state.allocation_view_path = selected_path

    # 新增輸入模式切換
    allocation_mode = st.radio("配置輸入模式", options=["百分比", "份額"], index=0, key="allocation_mode")
    st.session_state.allocation_mode = allocation_mode

    path: list[str] = selected_path.split(" -> ") if selected_path != "投資組合" else []
    if allocation_mode == "百分比":
        _render_asset_allocator_recursive(portfolio_state, path)
    else:
        _render_asset_allocator_shares(portfolio_state, path)

def _render_asset_allocator_recursive(portfolio_state: PortfolioState, path: list[str]) -> None:
    """以遞迴方式渲染下層資產節點"""
    if current := portfolio_state.get_node_by_path(path):
        if current.has_children:
            for name in hierarchy_manager.get_sorted_children(current):
                if name in current.children:
                    _render_asset_item(portfolio_state, path, name)

# 新增份額模式的資產配置遞迴函式
def _render_asset_allocator_shares(portfolio_state: PortfolioState, path: list[str]) -> None:
    """以份額輸入方式渲染當前層次配置，並依輸入份額計算百分比"""
    if current := portfolio_state.get_node_by_path(path):
        if current.has_children:
            st.write("配置設定（份額模式）：")
            for name in hierarchy_manager.get_sorted_children(current):
                if name not in current.children:
                    continue
                asset_node = current.children[name]
                cols = st.columns([5, 1, 1])
                share_key = f"share_{'_'.join(path) or 'root'}_{name}"
                default_share = st.session_state.get(share_key, 1)
                with cols[0]:
                    new_share = st.number_input(
                        label=f"{name} (份額)",
                        min_value=0,
                        step=1,
                        value=default_share,
                        key=share_key,
                    )
                with cols[1]:
                    # 鎖定/解鎖按鈕
                    current_fixed = portfolio_state.is_fixed(path, name)
                    if st.button(
                        "🔒" if current_fixed else "🔓",
                        key=f"fixed_{name}_{'_'.join(path)}",
                        help="點擊切換鎖定狀態",
                    ):
                        portfolio_state.toggle_fixed(path, name, not current_fixed)
                        st.rerun()
                with cols[2]:
                    # 刪除按鈕
                    if st.button(
                        "🗑️",
                        key=f"del_{name}_{'_'.join(path)}",
                        help="點擊刪除該項資產",
                    ):
                        if portfolio_state.remove_asset(path + [name]):
                            st.rerun()
            # 按鈕：更新當前層次所有子節點的份額配置
            if st.button("確認更新份額配置", key=f"update_share_{'_'.join(path) or 'root'}"):
                total_shares = 0
                share_values = {}
                for name in current.children.keys():
                    share_key = f"share_{'_'.join(path) or 'root'}_{name}"
                    share_val = st.session_state.get(share_key, 0)
                    share_values[name] = share_val
                    total_shares += share_val
                if total_shares > 0:
                    for name, share in share_values.items():
                        new_percentage = (share / total_shares) * 100
                        portfolio_state.update_allocation(path, name, new_percentage)
                    st.success("更新份額配置成功！")
                    st.rerun()
        # 遞迴處理下一層
        for name in hierarchy_manager.get_sorted_children(current):
            if name in current.children:
                asset_node = current.children[name]
                if asset_node.has_children:
                    st.markdown(f"#### {name} 子項配置")
                    _render_asset_allocator_shares(portfolio_state, path + [name])

class AssetItemState:
    def __init__(self, portfolio_state: PortfolioState, path: list[str], name: str):
        self.portfolio_state = portfolio_state
        self.path = path
        self.name = name
        self.current = portfolio_state.get_node_by_path(path)
        self.allocation = portfolio_state.get_allocation(path, name)
        self.is_fixed = portfolio_state.is_fixed(path, name)

        self.total_items = len(self.current.allocation_group.allocations) if self.current else 0
        self.fixed_count = len(self.current.allocation_group.fixed_items) if self.current else 0
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

    def get_fixed_help(self) -> str:
        if self.is_single_asset:
            return "單一資產無法鎖定"
        if self.is_fixed:
            all_fixed = self.fixed_count == self.total_items
            return "點擊解除鎖定" + (" (同時解除其他鎖定項目)" if all_fixed else "")
        is_last_two = self.unfixed_count == 2
        return "點擊鎖定" + (" (同時鎖定其他項目)" if is_last_two else "")

    def get_delete_help(self) -> str:
        return "已鎖定項目不可刪除" if self.is_fixed else None

def _render_asset_item(portfolio_state: PortfolioState, path: list[str], name: str) -> None:
    """渲染單一資產配置項目，包括數字調整與鎖定/刪除按鈕"""
    state = AssetItemState(portfolio_state, path, name)
    total_weight = portfolio_state.get_total_weight(path + [name])

    cols = st.columns([5, 1, 1])
    # 將提示訊息重構，提升可讀性
    locked_text = " (已鎖定)" if state.is_fixed else ""
    unique_text = " (僅此一項)" if state.is_single_asset else ""
    slider_help = f"局部比例：{state.allocation:.1f}%\n總體比例：{total_weight:.1f}%{locked_text}{unique_text}"
    new_value = cols[0].number_input(
        label=f"**{name}** (%)",
        min_value=0,
        max_value=100,
        step=10,
        value=int(round(state.allocation)),
        disabled=state.slider_disabled,
        help=slider_help,
    )
    if new_value != state.allocation:
        portfolio_state.update_allocation(path, name, float(new_value))
        st.rerun()

    cols[1].write("")
    cols[1].write("")
    if cols[1].button(
        state.fixed_label,
        key=f"fixed_{name}",
        help=state.get_fixed_help(),
        disabled=state.fixed_disabled,
    ):
        portfolio_state.toggle_fixed(path, name, not state.is_fixed)
        st.rerun()

    cols[2].write("")
    cols[2].write("")
    if cols[2].button(
        "🗑️",
        key=f"del_{name}",
        disabled=state.delete_disabled,
        help=state.get_delete_help(),
    ):
        if portfolio_state.remove_asset(path + [name]):
            st.rerun()
