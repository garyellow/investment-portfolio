import streamlit as st

from src.models.enums import NodeType
from src.models.portfolio import PortfolioState


def render_rebalancer_ui(portfolio_state: PortfolioState) -> None:
    """
    渲染資產再平衡介面，依目標比例計算推薦買入或賣出金額。
    """
    st.header("🔄 資產再平衡計算")
    st.write("請輸入各資產（標的）的現有市值，系統將依預定比例計算推薦操作，確保資料單位一致。")

    terminal_types = {
        NodeType.CASH_SYMBOL,
        NodeType.ETF_SYMBOL,
        NodeType.STOCK_SYMBOL,
        NodeType.FUND_SYMBOL,
        NodeType.CRYPTO_SYMBOL,
        NodeType.OTHER_SYMBOL,
    }
    terminal_nodes = [
        node for node in portfolio_state.get_all_nodes() if node.node_type in terminal_types
    ]

    st.write("※ 請確認所有金額單位一致")
    current_values = {}
    with st.form("rebalancing_form"):
        for node in terminal_nodes:
            key = node.full_path
            current_values[key] = st.number_input(f"{key} 的現有市值", value=0.0, step=0.1, key=key)
        submitted = st.form_submit_button("開始計算推薦")

    if submitted:
        total_value = sum(current_values.values())
        st.write(f"總市值：{total_value:.2f}")
        if total_value == 0:
            st.warning("所有市值皆為0，無法計算建議")
            return
        st.subheader("調整建議")
        for node in terminal_nodes:
            path_list = node.full_path.split(" -> ")
            weight = portfolio_state.get_total_weight(path_list)
            target_value = total_value * (weight / 100)
            diff = target_value - current_values[node.full_path]
            suggestion = "買入" if diff > 0 else "賣出" if diff < 0 else "保持"
            st.write(f"{node.full_path}：目標比例 {weight:.2f}%，現有市值 {current_values[node.full_path]:.2f}，目標市值 {target_value:.2f}，建議{suggestion} {abs(diff):.2f}")
