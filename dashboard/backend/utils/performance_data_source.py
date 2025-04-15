import json
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from hummingbot.core.data_type.common import TradeType
from hummingbot.strategy_v2.models.base import RunnableStatus
from hummingbot.strategy_v2.models.executors import CloseType
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


class PerformanceDataSource:
    def __init__(self, checkpoint_data: Dict[str, Any]):
        if not checkpoint_data or not isinstance(checkpoint_data, dict):
            raise ValueError("Invalid checkpoint data provided")

        # 适配表名大小写
        self._adapt_table_names(checkpoint_data)

        # 验证必要的字段是否存在
        required_fields = ["executors", "orders", "trade_fill", "controllers"]
        missing_fields = [field for field in required_fields if field not in checkpoint_data]
        if missing_fields:
            raise ValueError(f"Checkpoint data is missing required fields: {', '.join(missing_fields)}")

        self.checkpoint_data = checkpoint_data

        # 确保各字段是有效的数据结构
        if not isinstance(self.checkpoint_data["executors"], (list, dict)):
            raise ValueError("Executors data is not valid")
        if not isinstance(self.checkpoint_data["orders"], (list, dict)):
            raise ValueError("Orders data is not valid")
        if not isinstance(self.checkpoint_data["trade_fill"], (list, dict)):
            raise ValueError("Trade fill data is not valid")
        if not isinstance(self.checkpoint_data["controllers"], (list, dict)):
            raise ValueError("Controllers data is not valid")

        self.executors_dict = self.checkpoint_data["executors"].copy()

        try:
            self.orders = self.load_orders()
            self.controllers_df = self.load_controllers()
            self.executors_with_orders = self.get_executors_with_orders(self.get_executors_df(), self.orders)
        except Exception as e:
            raise ValueError(f"Error initializing performance data source: {str(e)}")

    def _adapt_table_names(self, data: Dict[str, Any]):
        """适配不同大小写的表名，通用处理方式，不限于特定表名"""
        # 存储所有小写表名，避免重复处理
        lowercase_keys = set(k.lower() for k in data.keys())

        # 查找并转换大写开头的表名
        keys_to_process = list(data.keys())
        for key in keys_to_process:
            # 如果表名是大写开头，且其小写版本不在字典中
            lowercase_key = key.lower()
            if key[0].isupper() and lowercase_key not in data:
                # 转换为全小写版本
                data[lowercase_key] = data.pop(key)

        # 特殊处理：确保关键表名存在且为小写
        required_fields = ["executors", "orders", "trade_fill", "controllers"]
        for field in required_fields:
            # 查找任何大小写变体
            variants = [k for k in data.keys() if k.lower() == field]
            if variants and field not in data:
                # 使用找到的变体，转换为标准小写形式
                data[field] = data.pop(variants[0])

    def load_orders(self):
        """
        Load the orders data from the checkpoint.
        """
        try:
            orders = self.checkpoint_data["orders"].copy()
            if not orders:
                return pd.DataFrame()  # 返回空DataFrame

            orders = pd.DataFrame(orders)
            return orders
        except Exception as e:
            raise ValueError(f"Error loading orders data: {str(e)}")

    def load_trade_fill(self):
        try:
            trade_fill = self.checkpoint_data["trade_fill"].copy()
            if not trade_fill:
                return pd.DataFrame()  # 返回空DataFrame

            trade_fill = pd.DataFrame(trade_fill)

            # 安全处理timestamp
            if "timestamp" in trade_fill.columns:
                trade_fill["timestamp"] = trade_fill["timestamp"].apply(
                    lambda x: self.ensure_timestamp_in_seconds(x) if x is not None else None
                )
                trade_fill["datetime"] = pd.to_datetime(trade_fill.timestamp, unit="s", errors="coerce")

            return trade_fill
        except Exception as e:
            raise ValueError(f"Error loading trade fill data: {str(e)}")

    def load_controllers(self):
        try:
            controllers = self.checkpoint_data["controllers"].copy()
            if not controllers:
                return pd.DataFrame()  # 返回空DataFrame

            controllers = pd.DataFrame(controllers)

            # 安全处理config字段
            if "config" in controllers.columns:
                controllers["config"] = controllers["config"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, dict) else {})
                )

            # 安全处理timestamp
            if "timestamp" in controllers.columns:
                controllers["datetime"] = pd.to_datetime(controllers.timestamp, unit="s", errors="coerce")

            return controllers
        except Exception as e:
            raise ValueError(f"Error loading controllers data: {str(e)}")

    @property
    def controllers_dict(self):
        try:
            if self.controllers_df.empty:
                return {}
            return {
                controller["id"]: controller["config"]
                for controller in self.controllers_df.to_dict(orient="records")
                if "id" in controller and "config" in controller
            }
        except Exception:
            return {}

    def get_executors_df(self, executors_filter: Optional[Dict[str, Any]] = None, apply_executor_data_types: bool = False):
        try:
            if not self.executors_dict:
                return pd.DataFrame()  # 返回空DataFrame

            executors_df = pd.DataFrame(self.executors_dict)

            # 安全处理各字段
            # 处理custom_info和config字段
            if "custom_info" in executors_df.columns:
                executors_df["custom_info"] = executors_df["custom_info"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, dict) else {})
                )
            else:
                executors_df["custom_info"] = [{} for _ in range(len(executors_df))]

            if "config" in executors_df.columns:
                executors_df["config"] = executors_df["config"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, dict) else {})
                )
            else:
                executors_df["config"] = [{} for _ in range(len(executors_df))]

            # 安全处理timestamp
            if "timestamp" in executors_df.columns:
                executors_df["timestamp"] = executors_df["timestamp"].apply(
                    lambda x: self.ensure_timestamp_in_seconds(x) if x is not None else None
                )

            if "close_timestamp" in executors_df.columns:
                executors_df["close_timestamp"] = executors_df["close_timestamp"].apply(
                    lambda x: self.ensure_timestamp_in_seconds(x) if x is not None else None
                )

            executors_df = executors_df.sort_values("close_timestamp", inplace=False)

            # 安全获取trading_pair和exchange
            if "config" in executors_df.columns:
                executors_df["trading_pair"] = executors_df["config"].apply(
                    lambda x: x.get("trading_pair", "") if isinstance(x, dict) else ""
                )
                executors_df["exchange"] = executors_df["config"].apply(
                    lambda x: x.get("connector_name", "") if isinstance(x, dict) else ""
                )

            # 安全处理status
            if "status" in executors_df.columns:
                executors_df["status"] = executors_df["status"].apply(
                    lambda x: int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else 0
                )

            # 确保数值型字段使用正确的数据类型，避免cumsum错误
            numeric_columns = ["net_pnl_pct", "net_pnl_quote", "cum_fees_quote", "filled_amount_quote"]
            for col in numeric_columns:
                if col in executors_df.columns:
                    executors_df[col] = pd.to_numeric(executors_df[col], errors="coerce").fillna(0.0)

            # 安全获取level_id
            if "config" in executors_df.columns:
                executors_df["level_id"] = executors_df["config"].apply(
                    lambda x: x.get("level_id", "") if isinstance(x, dict) else ""
                )

            # 安全获取其他字段
            if "custom_info" in executors_df.columns:
                executors_df["bep"] = executors_df["custom_info"].apply(
                    lambda x: x.get("current_position_average_price", 0) if isinstance(x, dict) else 0
                )
                executors_df["order_ids"] = executors_df["custom_info"].apply(
                    lambda x: x.get("order_ids", []) if isinstance(x, dict) else []
                )
                executors_df["close_price"] = executors_df["custom_info"].apply(
                    lambda x: x.get("close_price", x.get("current_position_average_price", 0)) if isinstance(x, dict) else 0
                )

            # 安全获取sl, tp, tl
            if "config" in executors_df.columns:
                executors_df["sl"] = (
                    executors_df["config"].apply(lambda x: x.get("stop_loss", 0) if isinstance(x, dict) else 0).fillna(0)
                )
                executors_df["tp"] = (
                    executors_df["config"].apply(lambda x: x.get("take_profit", 0) if isinstance(x, dict) else 0).fillna(0)
                )
                executors_df["tl"] = (
                    executors_df["config"].apply(lambda x: x.get("time_limit", 0) if isinstance(x, dict) else 0).fillna(0)
                )

            # 安全处理close_type_name
            if "close_type" in executors_df.columns:
                executors_df["close_type_name"] = executors_df["close_type"].apply(
                    lambda x: self.get_enum_by_value_safe(CloseType, x).name if x is not None else "UNKNOWN"
                )

            # 合并controllers数据
            if not self.controllers_df.empty and "controller_id" in executors_df.columns:
                controllers = self.controllers_df.copy()
                if "controller_id" in controllers.columns:
                    controllers.drop(columns=["controller_id"], inplace=True, errors="ignore")
                    controllers.rename(
                        columns={"config": "controller_config", "type": "controller_type", "id": "controller_id"}, inplace=True
                    )

                    # 安全合并
                    try:
                        executors_df = executors_df.merge(
                            controllers[["controller_id", "controller_type", "controller_config"]], on="controller_id", how="left"
                        )
                    except Exception:
                        # 如果合并失败，添加空列
                        executors_df["controller_type"] = ""
                        executors_df["controller_config"] = [{} for _ in range(len(executors_df))]

            if apply_executor_data_types:
                executors_df = self.apply_executor_data_types(executors_df)
            if executors_filter is not None:
                executors_df = self.filter_executors(executors_df, executors_filter)
            return executors_df
        except Exception as e:
            # 出错时返回空DataFrame
            import traceback

            print(f"Error in get_executors_df: {str(e)}")
            print(traceback.format_exc())
            return pd.DataFrame()

    def apply_executor_data_types(self, executors):
        try:
            if executors.empty:
                return executors

            # 确保数值型字段使用正确的数据类型，避免cumsum错误
            numeric_columns = ["net_pnl_pct", "net_pnl_quote", "cum_fees_quote", "filled_amount_quote"]
            for col in numeric_columns:
                if col in executors.columns:
                    executors[col] = pd.to_numeric(executors[col], errors="coerce").fillna(0.0)

            # 安全转换status
            if "status" in executors.columns:
                executors["status"] = executors["status"].apply(
                    lambda x: self.get_enum_by_value_safe(
                        RunnableStatus, int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else 0
                    )
                )

            # 安全转换side
            if "config" in executors.columns:
                executors["side"] = executors["config"].apply(
                    lambda x: self.get_enum_by_value_safe(
                        TradeType, int(x.get("side", 0)) if isinstance(x, dict) and x.get("side") is not None else 0
                    )
                )

            # 安全转换close_type
            if "close_type" in executors.columns:
                executors["close_type"] = executors["close_type"].apply(
                    lambda x: self.get_enum_by_value_safe(
                        CloseType, int(x) if isinstance(x, (int, float, str)) and str(x).isdigit() else 0
                    )
                )

            # 安全转换datetime
            if "timestamp" in executors.columns:
                executors["datetime"] = pd.to_datetime(executors.timestamp, unit="s", errors="coerce")

            if "close_timestamp" in executors.columns:
                executors["close_datetime"] = pd.to_datetime(executors["close_timestamp"], unit="s", errors="coerce")

            return executors
        except Exception as e:
            print(f"Error in apply_executor_data_types: {str(e)}")
            return executors

    @staticmethod
    def remove_executor_data_types(executors):
        try:
            if executors.empty:
                return executors

            # 安全转换status, side, close_type
            if "status" in executors.columns:
                executors["status"] = executors["status"].apply(lambda x: x.value if hasattr(x, "value") else 0)

            if "side" in executors.columns:
                executors["side"] = executors["side"].apply(lambda x: x.value if hasattr(x, "value") else 0)

            if "close_type" in executors.columns:
                executors["close_type"] = executors["close_type"].apply(lambda x: x.value if hasattr(x, "value") else 0)

            # 删除日期时间列
            executors.drop(columns=["datetime", "close_datetime"], inplace=True, errors="ignore")

            return executors
        except Exception as e:
            print(f"Error in remove_executor_data_types: {str(e)}")
            return executors

    @staticmethod
    def get_executors_with_orders(executors_df: pd.DataFrame, orders: pd.DataFrame):
        try:
            if executors_df.empty or orders.empty:
                return pd.DataFrame()  # 返回空DataFrame

            # 确保必要的列存在
            if "id" not in executors_df.columns or "order_ids" not in executors_df.columns:
                return pd.DataFrame()

            if "client_order_id" not in orders.columns:
                return pd.DataFrame()

            df = (
                executors_df[["id", "order_ids"]]
                .rename(columns={"id": "executor_id", "order_ids": "order_id"})
                .explode("order_id")
            )

            exec_with_orders = df.merge(orders, left_on="order_id", right_on="client_order_id", how="inner")

            # 过滤订单状态
            if "last_status" in exec_with_orders.columns:
                exec_with_orders = exec_with_orders[
                    exec_with_orders["last_status"].isin(["SellOrderCompleted", "BuyOrderCompleted"])
                ]

            # 选择所需列
            result_columns = ["executor_id", "order_id", "last_status", "last_update_timestamp", "price", "amount", "position"]
            available_columns = [col for col in result_columns if col in exec_with_orders.columns]

            if not available_columns:
                return pd.DataFrame()

            return exec_with_orders[available_columns]
        except Exception as e:
            print(f"Error in get_executors_with_orders: {str(e)}")
            return pd.DataFrame()

    def get_executor_info_list(self, executors_filter: Optional[Dict[str, Any]] = None) -> List[ExecutorInfo]:
        try:
            required_columns = [
                "id",
                "timestamp",
                "type",
                "close_timestamp",
                "close_type",
                "status",
                "controller_type",
                "net_pnl_pct",
                "net_pnl_quote",
                "cum_fees_quote",
                "filled_amount_quote",
                "is_active",
                "is_trading",
                "controller_id",
                "side",
                "config",
                "custom_info",
                "exchange",
                "trading_pair",
            ]

            executors_df = self.get_executors_df(executors_filter=executors_filter, apply_executor_data_types=True)

            if executors_df.empty:
                return []

            # 确保所需列存在
            missing_columns = [col for col in required_columns if col not in executors_df.columns]
            if missing_columns:
                for col in missing_columns:
                    if col == "net_pnl_pct" or col == "net_pnl_quote" or col == "cum_fees_quote" or col == "filled_amount_quote":
                        executors_df[col] = 0.0
                    elif col == "is_active" or col == "is_trading":
                        executors_df[col] = False
                    else:
                        executors_df[col] = None

            # 过滤并安全获取数据
            available_columns = [col for col in required_columns if col in executors_df.columns]
            filtered_executors_df = executors_df[available_columns].copy()

            # 过滤net_pnl_quote不为0的记录
            if "net_pnl_quote" in filtered_executors_df.columns:
                filtered_executors_df = filtered_executors_df[filtered_executors_df["net_pnl_quote"] != 0]

            # 创建ExecutorInfo对象
            executor_info_list = []
            for _, row in filtered_executors_df.iterrows():
                try:
                    executor_info = ExecutorInfo(**row.to_dict())
                    executor_info_list.append(executor_info)
                except Exception:
                    continue

            return executor_info_list
        except Exception as e:
            print(f"Error in get_executor_info_list: {str(e)}")
            return []

    def get_executor_dict(
        self,
        executors_filter: Optional[Dict[str, Any]] = None,
        apply_executor_data_types: bool = False,
        remove_special_fields: bool = False,
    ) -> List[dict]:
        try:
            executors_df = self.get_executors_df(executors_filter, apply_executor_data_types=apply_executor_data_types).copy()
            if executors_df.empty:
                return []

            if remove_special_fields:
                executors_df = self.remove_executor_data_types(executors_df)

            return executors_df.to_dict(orient="records")
        except Exception as e:
            print(f"Error in get_executor_dict: {str(e)}")
            return []

    def get_executors_by_controller_type(self, executors_filter: Optional[Dict[str, Any]] = None) -> Dict[str, pd.DataFrame]:
        try:
            executors_by_controller_type = {}
            executors_df = self.get_executors_df(executors_filter).copy()

            if executors_df.empty or "controller_type" not in executors_df.columns:
                return {}

            for controller_type in executors_df["controller_type"].unique():
                if pd.isna(controller_type):
                    continue
                executors_by_controller_type[controller_type] = executors_df[executors_df["controller_type"] == controller_type]
            return executors_by_controller_type
        except Exception as e:
            print(f"Error in get_executors_by_controller_type: {str(e)}")
            return {}

    @staticmethod
    def filter_executors(executors_df: pd.DataFrame, filters: Dict[str, List[Any]]):
        try:
            if executors_df.empty:
                return executors_df

            filter_condition = np.array([True] * len(executors_df))
            for key, value in filters.items():
                if key not in executors_df.columns:
                    continue

                if isinstance(value, list) and len(value) > 0:
                    filter_condition &= np.array(executors_df[key].isin(value))
                elif key == "start_time" and value is not None:
                    if "timestamp" in executors_df.columns:
                        filter_condition &= np.array(executors_df["timestamp"] >= value - 60)
                elif key == "close_type_name" and value is not None:
                    if "close_type_name" in executors_df.columns:
                        filter_condition &= np.array(executors_df["close_type_name"] == value)
                elif key == "end_time" and value is not None:
                    if "close_timestamp" in executors_df.columns:
                        filter_condition &= np.array(executors_df["close_timestamp"] <= value + 60)

            return executors_df[filter_condition]
        except Exception as e:
            print(f"Error in filter_executors: {str(e)}")
            return executors_df

    @staticmethod
    def get_enum_by_value(enum_class, value):
        for member in enum_class:
            if member.value == value:
                return member
        raise ValueError(f"No enum member with value {value}")

    @staticmethod
    def get_enum_by_value_safe(enum_class, value):
        """安全的枚举值获取，出错时返回第一个枚举值"""
        try:
            for member in enum_class:
                if member.value == value:
                    return member
            # 如果找不到匹配的值，返回第一个成员
            return next(iter(enum_class))
        except Exception:
            # 如果发生任何错误，返回第一个成员
            try:
                return next(iter(enum_class))
            except Exception:
                # 如果连第一个成员都无法获取，则返回None
                return None

    @staticmethod
    def ensure_timestamp_in_seconds(timestamp: Any) -> float:
        """
        确保给定时间戳以秒为单位。
        """
        try:
            if timestamp is None:
                return 0.0

            if isinstance(timestamp, str) and not timestamp.strip():
                return 0.0

            timestamp_float = float(timestamp)
            timestamp_int = int(timestamp_float)

            if timestamp_int >= 1e18:  # 纳秒
                return timestamp_int / 1e9
            elif timestamp_int >= 1e15:  # 微秒
                return timestamp_int / 1e6
            elif timestamp_int >= 1e12:  # 毫秒
                return timestamp_int / 1e3
            elif timestamp_int >= 1e9:  # 秒
                return timestamp_int
            else:
                return timestamp_float  # 假设已经是秒
        except (ValueError, TypeError):
            return 0.0  # 转换失败时返回0
