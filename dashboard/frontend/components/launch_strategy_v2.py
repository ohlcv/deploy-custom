import time

import streamlit as st
from streamlit_elements import lazy, mui

from ..st_utils import get_backend_api_client
from ..utils.i18n import t
from .dashboard import Dashboard


class LaunchStrategyV2(Dashboard.Item):
    DEFAULT_ROWS = []
    DEFAULT_COLUMNS = [
        {
            "field": "config_base",
            "headerName": t("Config Base"),
            "minWidth": 160,
            "editable": False,
        },
        {
            "field": "version",
            "headerName": t("Version"),
            "minWidth": 100,
            "editable": False,
        },
        {
            "field": "controller_name",
            "headerName": t("Controller Name"),
            "width": 150,
            "editable": False,
        },
        {
            "field": "controller_type",
            "headerName": t("Controller Type"),
            "width": 150,
            "editable": False,
        },
        {
            "field": "connector_name",
            "headerName": t("Connector"),
            "width": 150,
            "editable": False,
        },
        {
            "field": "trading_pair",
            "headerName": t("Trading pair"),
            "width": 140,
            "editable": False,
        },
        {
            "field": "total_amount_quote",
            "headerName": t("Total amount ($)"),
            "width": 140,
            "editable": False,
        },
        {
            "field": "max_loss_quote",
            "headerName": t("Max loss ($)"),
            "width": 120,
            "editable": False,
        },
        {
            "field": "stop_loss",
            "headerName": t("SL (%)"),
            "width": 100,
            "editable": False,
        },
        {
            "field": "take_profit",
            "headerName": t("TP (%)"),
            "width": 100,
            "editable": False,
        },
        {
            "field": "trailing_stop",
            "headerName": t("TS (%)"),
            "width": 120,
            "editable": False,
        },
        {
            "field": "time_limit",
            "headerName": t("Time limit"),
            "width": 100,
            "editable": False,
        },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._backend_api_client = get_backend_api_client()
        self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
        self._controller_config_selected = None
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
        self._credentials = "master_account"
        self._max_global_drawdown = None
        self._max_controller_drawdown = None
        self._rebalance_interval = None
        self._asset_to_rebalance = "USDT"

        # 初始化或重置配置选择状态
        st.session_state["config_selection_status"] = "None"

    def _set_bot_name(self, event):
        self._bot_name = event.target.value

    def _set_image_name(self, _, childs):
        self._image_name = childs.props.value

    def _set_credentials(self, _, childs):
        self._credentials = childs.props.value

    def _set_controller(self, event):
        self._controller_selected = event.target.value

    def _handle_row_selection(self, params, _):
        """处理行选择事件，在MUI DataGrid中，params是选中行的ID列表"""
        # 不再显示选中的行信息和处理后的配置

        # 重写处理逻辑，直接使用params作为选中的ID列表
        if params and len(params) > 0:
            # 确保params中的值是字符串而不是其他类型
            self._controller_config_selected = [f"{str(param)}.yml" for param in params]
            # 更新配置添加状态，实时显示选中的配置数量
            st.session_state["config_selection_status"] = f"{len(params)}"  # 只显示数字
        else:
            self._controller_config_selected = []
            # 如果没有选择配置，显示None状态
            st.session_state["config_selection_status"] = "0"  # 显示0而不是None

    def _set_max_global_drawdown(self, event):
        self._max_global_drawdown = event.target.value

    def _set_max_controller_drawdown(self, event):
        self._max_controller_drawdown = event.target.value

    def _set_rebalance_interval(self, event):
        self._rebalance_interval = event.target.value

    def _set_asset_to_rebalance(self, event):
        self._asset_to_rebalance = event.target.value

    def launch_new_bot(self):
        if not self._bot_name:
            st.warning(t("You need to define the bot name."))
            return
        if not self._image_name:
            st.warning(t("You need to select the hummingbot image."))
            return
        if not self._controller_config_selected or len(self._controller_config_selected) == 0:
            st.warning(
                t(
                    "You need to select the controllers configs. Please select at least one controller config by clicking on the checkbox."
                )
            )
            return

        try:
            # 显示处理中状态
            with st.spinner("正在准备配置..."):
                start_time_str = time.strftime("%Y.%m.%d_%H.%M")
                bot_name = f"{self._bot_name}-{start_time_str}"
                script_config = {
                    "name": bot_name,
                    "content": {
                        "markets": {},
                        "candles_config": [],
                        "controllers_config": self._controller_config_selected,
                        "config_update_interval": 10,
                        "script_file_name": "v2_with_controllers.py",
                        "time_to_cash_out": None,
                    },
                }
                if self._max_global_drawdown:
                    script_config["content"]["max_global_drawdown"] = self._max_global_drawdown
                if self._max_controller_drawdown:
                    script_config["content"]["max_controller_drawdown"] = self._max_controller_drawdown
                if self._rebalance_interval:
                    script_config["content"]["rebalance_interval"] = self._rebalance_interval
                    if self._asset_to_rebalance and "USD" in self._asset_to_rebalance:
                        script_config["content"]["asset_to_rebalance"] = self._asset_to_rebalance
                    else:
                        st.error(t("You need to define the asset to rebalance in USD like token."))
                        return

            # 清理现有配置
            with st.spinner("正在清理旧配置..."):
                delete_response = self._backend_api_client.delete_all_script_configs()
                if delete_response and delete_response.get("status") == "error":
                    st.error(f"清理旧配置失败: {delete_response.get('detail', '未知错误')}")
                    return

            # 添加新配置
            with st.spinner("正在添加新配置..."):
                # 记录配置信息
                st.session_state["last_script_config"] = script_config

                add_config_response = self._backend_api_client.add_script_config(script_config)

                if not add_config_response:
                    st.error("配置添加失败: API返回空响应")
                    return

                if add_config_response.get("status") == "error":
                    st.error(f"配置添加失败: {add_config_response.get('detail', '未知错误')}")
                    return

            # 创建实例
            with st.spinner("正在创建机器人实例..."):
                deploy_config = {
                    "instance_name": bot_name,
                    "script": "v2_with_controllers.py",
                    "script_config": bot_name + ".yml",
                    "image": self._image_name,
                    "credentials_profile": self._credentials,
                }

                # 记录部署配置
                st.session_state["last_deploy_config"] = deploy_config

                create_response = self._backend_api_client.create_hummingbot_instance(deploy_config)

                if not create_response:
                    st.error("实例创建失败: API返回空响应")
                    return

                if create_response.get("status") == "error":
                    st.error(f"实例创建失败: {create_response.get('detail', '未知错误')}")
                    return

            # 启动成功
            with st.spinner(t("Starting Bot... This process may take a few seconds")):
                time.sleep(3)

            # 直接使用streamlit的success组件而不是t()包装的文本，确保成功消息显示
            st.success("机器人已成功部署！您可以在实例页面查看其状态。")

            # 清空选择，为下一次部署做准备
            self._controller_config_selected = None
            self._bot_name = None

            # 重置状态
            st.session_state["config_selection_status"] = "None"

        except Exception as e:
            st.error(f"部署过程中发生错误: {str(e)}")
            # 记录错误信息
            st.session_state["deploy_error"] = str(e)

    def delete_selected_configs(self):
        if self._controller_config_selected:
            for config in self._controller_config_selected:
                response = self._backend_api_client.delete_controller_config(config)
                st.success(response)
            self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
        else:
            st.warning(t("You need to select the controllers configs that you want to delete."))

    def __call__(self):
        # 初始化配置选择状态，如果不存在
        if "config_selection_status" not in st.session_state:
            st.session_state["config_selection_status"] = "0"

        with mui.Paper(
            key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1
        ):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.Typography("🎛️ " + t("Bot Configuration"), variant="h5")

            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                with mui.Grid(item=True, xs=3):
                    mui.TextField(
                        label=t("Instance Name"), variant="outlined", onChange=lazy(self._set_bot_name), sx={"width": "100%"}
                    )
                with mui.Grid(item=True, xs=3):
                    available_images = self._backend_api_client.get_available_images("hummingbot")
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText(t("Available Images"))
                        with mui.Select(
                            label=t("Hummingbot Image"),
                            defaultValue="hummingbot/hummingbot:latest",
                            variant="standard",
                            onChange=lazy(self._set_image_name),
                        ):
                            for image in available_images:
                                mui.MenuItem(image, value=image)
                    available_credentials = self._backend_api_client.get_accounts()
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText(t("Credentials"))
                        with mui.Select(
                            label=t("Credentials"),
                            defaultValue="master_account",
                            variant="standard",
                            onChange=lazy(self._set_credentials),
                        ):
                            for master_config in available_credentials:
                                mui.MenuItem(master_config, value=master_config)
                with mui.Grid(item=True, xs=3):
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText(t("Risk Management"))
                        mui.TextField(
                            label=t("Max Global Drawdown (%)"),
                            variant="outlined",
                            type="number",
                            onChange=lazy(self._set_max_global_drawdown),
                            sx={"width": "100%"},
                        )
                        mui.TextField(
                            label=t("Max Controller Drawdown (%)"),
                            variant="outlined",
                            type="number",
                            onChange=lazy(self._set_max_controller_drawdown),
                            sx={"width": "100%"},
                        )

                with mui.Grid(item=True, xs=3):
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText(t("Rebalance Configuration"))
                        mui.TextField(
                            label=t("Rebalance Interval (minutes)"),
                            variant="outlined",
                            type="number",
                            onChange=lazy(self._set_rebalance_interval),
                            sx={"width": "100%"},
                        )
                        mui.TextField(
                            label=t("Asset to Rebalance"),
                            variant="outlined",
                            onChange=lazy(self._set_asset_to_rebalance),
                            sx={"width": "100%"},
                            default="USDT",
                        )
                all_controllers_config = self._backend_api_client.get_all_controllers_config()
                # 移除调试信息
                # st.write("API返回的控制器配置:")
                # st.write(f"数据类型: {type(all_controllers_config)}")
                # st.write(f"数据内容: {all_controllers_config}")

                data = []
                for config in all_controllers_config:
                    connector_name = config.get("connector_name", "Unknown")
                    trading_pair = config.get("trading_pair", "Unknown")

                    # 确保数值型字段为数字类型
                    total_amount_quote = config.get("total_amount_quote", 0)
                    if isinstance(total_amount_quote, str):
                        try:
                            total_amount_quote = float(total_amount_quote)
                        except (ValueError, TypeError):
                            total_amount_quote = 0

                    stop_loss = config.get("stop_loss", 0)
                    if isinstance(stop_loss, str):
                        try:
                            stop_loss = float(stop_loss)
                        except (ValueError, TypeError):
                            stop_loss = 0

                    take_profit = config.get("take_profit", 0)
                    if isinstance(take_profit, str):
                        try:
                            take_profit = float(take_profit)
                        except (ValueError, TypeError):
                            take_profit = 0

                    trailing_stop = config.get("trailing_stop", {"activation_price": 0, "trailing_delta": 0})
                    time_limit = config.get("time_limit", 0)
                    if isinstance(time_limit, str):
                        try:
                            time_limit = float(time_limit)
                        except (ValueError, TypeError):
                            time_limit = 0

                    config_version = config["id"].split("_")
                    if len(config_version) > 1:
                        config_base = config_version[0]
                        version = config_version[1]
                    else:
                        config_base = config["id"]
                        version = "NaN"
                    ts_text = str(trailing_stop["activation_price"]) + " / " + str(trailing_stop["trailing_delta"])
                    data.append(
                        {
                            "id": config["id"],
                            "config_base": config_base,
                            "version": version,
                            "controller_name": config["controller_name"],
                            "controller_type": config.get("controller_type", "generic"),
                            "connector_name": connector_name,
                            "trading_pair": trading_pair,
                            "total_amount_quote": total_amount_quote,
                            "max_loss_quote": total_amount_quote * stop_loss / 2,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "trailing_stop": ts_text,
                            "time_limit": time_limit,
                        }
                    )

                with mui.Grid(item=True, xs=12):
                    with mui.Paper(
                        key=self._key,
                        sx={
                            "display": "flex",
                            "flexDirection": "column",
                            "borderRadius": 3,
                            "overflow": "hidden",
                            "height": 1000,
                        },
                        elevation=2,
                    ):
                        with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                            with mui.Grid(container=True, spacing=2):
                                with mui.Grid(item=True, xs=8):
                                    # 显示标题，如果有选中的配置，显示配置数量
                                    selected_configs = st.session_state.get("config_selection_status", "0")
                                    mui.Typography(
                                        "🗄️ "
                                        + t("Available Configurations")
                                        + (f": 已选 {selected_configs} 个" if selected_configs != "0" else ""),
                                        variant="h6",
                                    )
                                with mui.Grid(item=True, xs=2):
                                    with mui.Button(
                                        onClick=self.delete_selected_configs,
                                        variant="outlined",
                                        color="error",
                                        sx={"width": "100%", "height": "100%"},
                                    ):
                                        mui.icon.Delete()
                                        mui.Typography(t("Delete"))
                                with mui.Grid(item=True, xs=2):
                                    with mui.Button(
                                        onClick=self.launch_new_bot,
                                        variant="outlined",
                                        color="success",
                                        sx={"width": "100%", "height": "100%"},
                                    ):
                                        mui.icon.AddCircleOutline()
                                        mui.Typography(t("Launch Bot"))
                        with mui.Box(sx={"flex": 1, "minHeight": 3, "width": "100%"}):
                            mui.DataGrid(
                                columns=self.DEFAULT_COLUMNS,
                                rows=data,
                                pageSize=15,
                                rowsPerPageOptions=[15],
                                checkboxSelection=True,
                                disableSelectionOnClick=True,
                                disableColumnResize=False,
                                onSelectionModelChange=self._handle_row_selection,
                                autoHeight=True,
                            )
