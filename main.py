import streamlit as st

from src.models.portfolio import PortfolioState
from src.ui.diagram import render_diagram
from src.ui.portfolio_ui import render_portfolio_ui
from src.ui.rebalancer import render_rebalancer_ui


def main() -> None:
    st.set_page_config(
        page_title="投資組合視覺化工具",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("💼 投資組合比例設定與視覺化")
    st.write("使用左側功能新增/調整資產，右側即時更新視覺化圖表。")

    st.session_state.setdefault("portfolio_state", PortfolioState())

    render_portfolio_ui(st.session_state.portfolio_state)
    render_diagram(st.session_state.portfolio_state)
    st.markdown("---")
    render_rebalancer_ui(st.session_state.portfolio_state)

if __name__ == "__main__":
    main()
