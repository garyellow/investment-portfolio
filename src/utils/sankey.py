from typing import NamedTuple

import plotly.graph_objects as go

from ..models.node import Node


class SankeyFlowData(NamedTuple):
    source_index: int
    target_index: int
    flow_value: float


class SankeyChart:
    def __init__(self):
        self.source_indices = []
        self.target_indices = []
        self.flow_values = []
        self.node_labels = []
        self.node_colors = []


def create_sankey_chart(node: Node) -> SankeyChart:
    chart = SankeyChart()
    asset_index_map = {}
    index_counter = 0

    def process_chart_node(node: Node, parent_index=None, cumulative_weight=100.0):
        nonlocal index_counter
        current_index = index_counter
        index_counter += 1

        asset_index_map[node] = current_index
        chart.node_labels.append(node.name)
        chart.node_colors.append(node.get_color())

        # 計算當前節點的權重
        if node.parent_node and node.parent_node.allocation_group:
            allocation = node.parent_node.allocation_group.get_allocation(
                node.name, 0.0
            )
            current_weight = cumulative_weight * allocation / 100.0
        else:
            current_weight = cumulative_weight

        if parent_index is not None:
            chart.source_indices.append(parent_index)
            chart.target_indices.append(current_index)
            chart.flow_values.append(current_weight)

        for child in node.children.values():
            process_chart_node(child, current_index, current_weight)

    process_chart_node(node)
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
