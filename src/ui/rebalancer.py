import streamlit as st
import pandas as pd

from src.models.enums import NodeType
from src.models.portfolio import PortfolioState


def render_rebalancer_ui(portfolio_state: PortfolioState) -> None:
    """
    渲染資產再平衡介面，依目標比例計算推薦買入或賣出金額。
    """
    # 新增：取得當前主題 (light 或 dark)
    theme = st.get_option("theme.base")

    st.markdown(
        '<h2 style="color:#1E90FF;">🔄 資產再平衡建議</h2>', unsafe_allow_html=True
    )
    st.write("根據目標配置，精算各資產調整建議，協助您優化組合。")

    terminal_types = {
        NodeType.CASH_SYMBOL,
        NodeType.ETF_SYMBOL,
        NodeType.STOCK_SYMBOL,
        NodeType.FUND_SYMBOL,
        NodeType.CRYPTO_SYMBOL,
        NodeType.OTHER_SYMBOL,
    }
    terminal_nodes = [
        node
        for node in portfolio_state.get_all_nodes()
        if node.node_type in terminal_types
    ]

    st.write("⚠️ 請以統一幣別輸入各項資產市值，以確保計算準確。")
    current_values = {}
    with st.form("rebalancing_form"):
        st.info("💡 系統將根據目標配置比例提供智能調整建議。")
        for node in terminal_nodes:
            key = node.full_path
            current_values[key] = st.number_input(
                f"💰 {key} 的現值",
                value=0,
                step=1000,
                key=key,
                help="請輸入該資產的當前市值",
            )
        submitted = st.form_submit_button("🎯 產生調整建議", use_container_width=True)

    if submitted:
        total_value = sum(current_values.values())
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💵 總資產規模", f"{total_value:,}")
        with col2:
            st.metric("📊 項目數量", f"{len(terminal_nodes)}")

        if total_value == 0:
            st.warning("⚠️ 請至少輸入一項資產的市值")
            return

        st.subheader("📝 資產調整建議")

        # 建立資料表
        rebalance_data = []
        for node in terminal_nodes:
            path_list = node.full_path.split(" -> ")
            weight = portfolio_state.get_total_weight(path_list)
            current_value = current_values[node.full_path]
            target_value = int(total_value * (weight / 100))
            diff = target_value - current_value
            progress = (current_value / target_value * 100) if target_value > 0 else 0

            rebalance_data.append(
                {
                    "資產名稱": node.full_path,
                    "目標比例": f"{weight:.1f}%",
                    "現有市值": current_value,
                    "目標市值": target_value,
                    "差額": diff,
                    "達成率": progress,
                }
            )

        df = pd.DataFrame(rebalance_data)

        # 顯示詳細的調整建議表格
        for _, row in df.iterrows():
            diff = row["差額"]
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {row['資產名稱']}")
                # 根據達成率設定不同顏色，依主題調整文字顏色
                progress_rate = row["達成率"]
                if theme == "dark":
                    if progress_rate > 100:
                        progress_color = "springgreen"
                    elif progress_rate >= 95:
                        progress_color = "deepskyblue"
                    else:
                        progress_color = "tomato"
                else:
                    if progress_rate > 100:
                        progress_color = "forestgreen"
                    elif progress_rate >= 95:
                        progress_color = "dodgerblue"
                    else:
                        progress_color = "tomato"

                progress_html = f"""
                <div style="color: {progress_color};">
                    達標率 {progress_rate:.1f}%
                </div>
                """
                st.progress(min(progress_rate, 100) / 100)
                st.markdown(progress_html, unsafe_allow_html=True)

            with col2:
                st.markdown("🎯 目標配置")
                st.write(f"配置比例：{row['目標比例']}")
                st.write(f"目標市值：{row['目標市值']:,}")

            with col3:
                st.markdown("💫 調整建議")
                diff_percentage = (
                    (abs(diff) / row["目標市值"] * 100)
                    if row["目標市值"] > 0
                    else float("inf")
                )

                if diff_percentage < 5:
                    st.success("✅ 建議維持現狀")
                elif diff > 0:
                    st.warning(f"⬆️ 建議買入 {abs(diff):,}")
                else:
                    st.error(f"⬇️ 建議賣出 {abs(diff):,}")

        # 顯示完整數據表格
        st.subheader("📊 組合分析表")

        # 自定義樣式函數，依主題設定不同背景色
        def highlight_progress(df):
            # 創建與 DataFrame 相同大小的空樣式 DataFrame
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            progress_values = df["達成率"].str.rstrip("%").astype(float)

            if theme == "dark":
                style_high = "background-color: #3CB371"  # mediumseagreen
                style_med = "background-color: #00BFFF"  # deepskyblue
                style_low = "background-color: #FF4500"  # orange red
            else:
                style_high = "background-color: #66CDAA"  # mediumaquamarine
                style_med = "background-color: #87CEFA"  # lightskyblue
                style_low = "background-color: #FF7F50"  # coral

            styles.loc[progress_values > 100, "達成率"] = style_high
            styles.loc[(progress_values >= 95) & (progress_values <= 100), "達成率"] = (
                style_med
            )
            styles.loc[progress_values < 95, "達成率"] = style_low
            return styles

        # 顯示格式化後的表格
        formatted_df = df.copy()
        formatted_df["達成率"] = formatted_df["達成率"].map("{:.1f}%".format)

        st.dataframe(
            formatted_df.style.format(
                {"現有市值": "{:,.0f}", "目標市值": "{:,.0f}", "差額": "{:,.0f}"}
            ).apply(highlight_progress, axis=None),
            hide_index=True,
        )
