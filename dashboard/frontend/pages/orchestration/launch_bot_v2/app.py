from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

from frontend.components.dashboard import Dashboard
from frontend.components.launch_strategy_v2 import LaunchStrategyV2
from frontend.st_utils import initialize_st_page, t

CARD_WIDTH = 6
CARD_HEIGHT = 3
NUM_CARD_COLS = 2

initialize_st_page(page_title=t("launch_bot_title"), icon="🙌")

if "launch_bots_board" not in st.session_state:
    board = Dashboard()
    launch_bots_board = SimpleNamespace(
        dashboard=board,
        launch_bot=LaunchStrategyV2(board, 0, 0, 12, 10),
    )
    st.session_state.launch_bots_board = launch_bots_board

else:
    launch_bots_board = st.session_state.launch_bots_board


with elements("create_bot"):
    with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
        with launch_bots_board.dashboard():
            launch_bots_board.launch_bot()
