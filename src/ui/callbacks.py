from typing import Callable

import streamlit as st

from ..models.portfolio import PortfolioState


def create_fixed_callback(
    portfolio_state: PortfolioState, path: list[str], name: str
) -> Callable[[], None]:
    """創建固定狀態切換回調"""

    def callback():
        key = f"fixed_{'_'.join(path + [name])}"
        if key in st.session_state:
            portfolio_state.toggle_fixed(path, name, st.session_state[key])
            st.rerun()

    return callback
