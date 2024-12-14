import streamlit as st

from ..models.hierarchy import hierarchy_manager
from ..models.portfolio import PortfolioState
from ..utils.sankey import create_sankey_chart, create_sankey_figure


def render_diagram(portfolio_state: PortfolioState) -> None:
    if not portfolio_state.root.has_children:
        st.info("尚未添加任何資產，請使用左側選單新增項目。")
        return

    st.header("📈 資產配置詳情")
    _render_asset_summary(portfolio_state)

    st.header("🌐 資產配置圖")
    sankey_chart = create_sankey_chart(portfolio_state.root)

    with st.expander("除錯資訊", expanded=False):
        st.write("節點數量:", len(sankey_chart.node_labels))
        st.write("連線數量:", len(sankey_chart.flow_values))
        st.write("節點標籤:", sankey_chart.node_labels)
        st.write("連線值:", sankey_chart.flow_values)

    st.plotly_chart(create_sankey_figure(sankey_chart), use_container_width=True)


def _render_asset_summary(portfolio_state: PortfolioState) -> None:
    for asset_type in hierarchy_manager.get_sorted_children(portfolio_state.root):
        if asset_type in portfolio_state.root.children:
            node = portfolio_state.root.children[asset_type]
            allocation = portfolio_state.get_allocation([], asset_type)

            with st.expander(f"**{asset_type}** （{allocation:.1f}%）"):
                if node.has_children:
                    _render_asset_type_details(portfolio_state, asset_type)
                else:
                    st.info(f"尚未添加任何 {asset_type} 標的")


def _render_asset_type_details(
    portfolio_state: PortfolioState, asset_type: str
) -> None:
    node = portfolio_state.root.children[asset_type]
    for sub_name, sub_node in sorted(node.children.items()):
        sub_allocation = portfolio_state.get_allocation([asset_type], sub_name)
        total_weight = portfolio_state.get_total_weight([asset_type, sub_name])

        st.write(
            f"  - **{sub_name}**：區域配置 {sub_allocation:.1f}% "
            f"(總體權重 {total_weight:.1f}%)"
        )

        if sub_node.has_children:
            for child_name in sorted(sub_node.children):
                child_allocation = portfolio_state.get_allocation(
                    [asset_type, sub_name], child_name
                )
                child_weight = portfolio_state.get_total_weight(
                    [asset_type, sub_name, child_name]
                )
                st.write(
                    f"    - {child_name}：區域配置 {child_allocation:.1f}% "
                    f"(總體權重 {child_weight:.1f}%)"
                )
