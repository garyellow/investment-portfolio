import plotly.graph_objects as go
import streamlit as st

from ..models.enums import get_color
from ..models.hierarchy import hierarchy_manager
from ..models.node import Node
from ..models.portfolio import PortfolioState


class SankeyChart:
    def __init__(self):
        self.source_indices = []
        self.target_indices = []
        self.flow_values = []
        self.node_labels = []
        self.node_colors = []


def create_sankey_chart(node: Node) -> SankeyChart:
    chart = SankeyChart()
    # 新增傳遞父節點的累計權重
    node_stack = [(node, -1, 100.0)]

    while node_stack:
        current, parent_idx, current_weight = node_stack.pop()
        current_idx = len(chart.node_labels)
        chart.node_labels.append(current.name)
        chart.node_colors.append(get_color(current.node_type))

        if parent_idx != -1:
            # 以傳入的 current_weight 作為該連線的 flow 值
            chart.flow_values.append(current_weight)
            chart.source_indices.append(parent_idx)
            chart.target_indices.append(current_idx)

        # 同步更新子節點的累計權重
        for child in reversed(list(current.children.values())):
            child_local_allocation = current.allocation_group.get_allocation(child.name, 0.0)
            child_weight = current_weight * child_local_allocation / 100.0
            node_stack.append((child, current_idx, child_weight))

    return chart


def create_sankey_figure(chart: SankeyChart, title: str = "投資組合分析") -> go.Figure:
    return go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="gray", width=0.5),
                    label=chart.node_labels,
                    color=chart.node_colors,
                    align="left",
                ),
                link=dict(
                    source=chart.source_indices,
                    target=chart.target_indices,
                    value=chart.flow_values,
                    color="rgba(160, 160, 160, 0.6)",
                    hovertemplate="%{source.label} ➡ %{target.label}<br />比例: %{value:.1f}%<extra></extra>",
                ),
            )
        ]
    ).update_layout(
        title=dict(
            text=title, font=dict(size=20, color="#FF4B4B"), x=0.5, xanchor="center"
        ),
        font=dict(size=12, family="Microsoft JhengHei"),
        height=600,
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
    )


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
