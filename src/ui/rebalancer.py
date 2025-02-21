import streamlit as st
import pandas as pd

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
            current_values[key] = st.number_input(f"{key} 的現有市值", value=0, step=1, key=key)
        submitted = st.form_submit_button("開始計算推薦")

    if submitted:
        total_value = sum(current_values.values())
        col1, col2 = st.columns(2)
        with col1:
            st.metric("投資組合總市值", f"{total_value:,}")
        with col2:
            st.metric("資產項目數量", f"{len(terminal_nodes)}")

        if total_value == 0:
            st.warning("所有市值皆為0，無法計算建議")
            return

        st.subheader("📊 調整建議總覽")

        # 建立資料表
        rebalance_data = []
        for node in terminal_nodes:
            path_list = node.full_path.split(" -> ")
            weight = portfolio_state.get_total_weight(path_list)
            current_value = current_values[node.full_path]
            target_value = int(total_value * (weight / 100))
            diff = target_value - current_value
            progress = (current_value / target_value * 100) if target_value > 0 else 0

            rebalance_data.append({
                "資產名稱": node.full_path,
                "目標比例": f"{weight:.1f}%",
                "現有市值": current_value,
                "目標市值": target_value,
                "差額": diff,
                "達成率": progress
            })

        df = pd.DataFrame(rebalance_data)

        # 顯示詳細的調整建議表格
        for _, row in df.iterrows():
            diff = row['差額']
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {row['資產名稱']}")
                progress_color = "normal" if 95 <= row['達成率'] <= 105 else "off"
                st.progress(min(row['達成率'], 100) / 100, text=f"達成率 {row['達成率']:.1f}%")

            with col2:
                st.markdown("**目標配置**")
                st.write(f"目標比例：{row['目標比例']}")
                st.write(f"目標市值：{row['目標市值']:,}")

            with col3:
                st.markdown("**調整建議**")
                if abs(diff) < total_value * 0.01:  # 差異小於1%視為達標
                    st.success("維持現狀 ✓")
                elif diff > 0:
                    st.warning(f"建議買入 {abs(diff):,} ↑")
                else:
                    st.error(f"建議賣出 {abs(diff):,} ↓")

        # 顯示完整數據表格
        st.subheader("📑 詳細數據表格")
        st.dataframe(
            df.style.format({
                "現有市值": "{:,.0f}",
                "目標市值": "{:,.0f}",
                "差額": "{:,.0f}",
                "達成率": "{:.1f}%"
            }),
            hide_index=True
        )
