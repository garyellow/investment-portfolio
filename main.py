import streamlit as st

from src.models.portfolio import PortfolioState
from src.ui.diagram import render_diagram
from src.ui.portfolio_ui import render_portfolio_ui
from src.ui.rebalancer import render_rebalancer_ui


def main() -> None:
    st.set_page_config(
        page_title="投資組合管理平台",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("💼 投資組合管理平台")

    # 注入自訂 CSS，根據主題切換顏色
    theme = st.get_option("theme.base")
    if theme == "dark":
        custom_css = """
        <style>
            h1, h2, h3 { color: #1E90FF; }
            /* 側邊欄背景：暗色 */
            .css-1d391kg { background-color: #333333; }
        </style>
        """
    else:
        custom_css = """
        <style>
            h1, h2, h3 { color: #1E90FF; }
            /* 側邊欄背景：亮色 */
            .css-1d391kg { background-color: #f9f9f9; }
        </style>
        """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.write("請從左側進行配置設定 👈")

    st.session_state.setdefault("portfolio_state", PortfolioState())

    render_portfolio_ui(st.session_state.portfolio_state)
    render_diagram(st.session_state.portfolio_state)
    st.markdown("---")
    render_rebalancer_ui(st.session_state.portfolio_state)


if __name__ == "__main__":
    main()
