from typing import Any, Dict, List, Optional
import urllib.parse
import time

import pandas as pd
import requests
import streamlit as st
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo
from requests.auth import HTTPBasicAuth


class BackendAPIClient:
    """
    This class is a client to interact with the backend API. The Backend API is a REST API that provides endpoints to
    create new Hummingbot instances, start and stop them, add new script and controller config files, and get the status
    of the active bots.
    """

    _shared_instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "BackendAPIClient":
        if cls._shared_instance is None:
            cls._shared_instance = BackendAPIClient(*args, **kwargs)
        return cls._shared_instance

    def __init__(self, host: str = "localhost", port: int = 8000, username: str = "admin", password: str = "admin"):
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.auth = HTTPBasicAuth(username, password)

    def post(self, endpoint: str, payload: Optional[Dict] = None, params: Optional[Dict] = None):
        """
        Post request to the backend API.
        :param params:
        :param endpoint:
        :param payload:
        :return:
        """
        url = f"{self.base_url}/{endpoint}"

        # 不再直接在页面上显示调试信息，统一使用API调试面板
        try:
            # 增加超时时间，容器操作可能需要更长时间
            response = requests.post(url, json=payload, params=params, auth=self.auth, timeout=30)
            result = self._process_response(response)

            # 添加调试信息更新
            try:
                # 导入更新调试信息的函数并调用
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "POST", payload, result)
            except Exception:
                # 导入失败或更新失败时不影响主流程
                pass

            return result
        except requests.exceptions.Timeout:
            response_data = {
                "status": "pending",
                "detail": "操作已提交，但服务器响应超时。这通常表示操作正在后台执行。请稍后刷新页面检查状态。",
            }

            # 超时也记录到调试信息
            try:
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "POST", payload, response_data)
            except Exception:
                pass

            return response_data
        except Exception as e:
            import traceback

            error_data = {"status": "error", "detail": f"Request error: {str(e)}", "traceback": traceback.format_exc()}

            # 错误也记录到调试信息
            try:
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "POST", payload, error_data)
            except Exception:
                pass

            return error_data

    def get(self, endpoint: str):
        """
        Get request to the backend API.
        :param endpoint:
        :return:
        """
        # 确保端点中的特殊字符被正确编码
        if "/" in endpoint:
            base_path, param = endpoint.split("/", 1)
            if "/" in param:
                base_path2, param2 = param.split("/", 1)
                endpoint = f"{base_path}/{base_path2}/{urllib.parse.quote(param2, safe='')}"
            else:
                endpoint = f"{base_path}/{urllib.parse.quote(param, safe='')}"

        url = f"{self.base_url}/{endpoint}"

        # 不再直接在页面上显示调试信息，统一使用API调试面板
        try:
            # 增加超时时间
            response = requests.get(url, auth=self.auth, timeout=20)
            result = self._process_response(response)

            # 添加调试信息更新
            try:
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "GET", None, result)
            except Exception:
                pass

            return result
        except requests.exceptions.Timeout:
            response_data = {"status": "pending", "detail": "请求超时，请稍后重试"}

            # 超时也记录到调试信息
            try:
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "GET", None, response_data)
            except Exception:
                pass

            return response_data
        except Exception as e:
            import traceback

            error_data = {"status": "error", "detail": f"Request error: {str(e)}", "traceback": traceback.format_exc()}

            # 错误也记录到调试信息
            try:
                from frontend.utils.api_debug import update_api_debug_info

                update_api_debug_info(endpoint, "GET", None, error_data)
            except Exception:
                pass

            return error_data

    @staticmethod
    def _process_response(response):
        """
        处理API响应，返回纯净的业务数据，不添加任何额外字段

        参数:
            response: HTTP响应对象

        返回:
            原始API响应数据，不包含任何额外添加的字段
        """
        try:
            # 处理错误响应
            if not response.ok:
                # 对于错误响应，我们确实需要返回错误信息
                status_code = response.status_code
                try:
                    if status_code == 401:
                        return {"status": "error", "detail": "Unauthorized access"}
                    elif status_code == 400:
                        try:
                            error_json = response.json()
                            error_detail = error_json.get("detail", "Bad request")
                        except:
                            error_detail = "无法解析错误详情"
                        return {"status": "error", "detail": error_detail}
                    elif status_code >= 500:
                        return {"status": "error", "detail": f"Server error: {status_code}"}
                    else:
                        return {"status": "error", "detail": f"Request failed: {status_code}"}
                except Exception as e:
                    return {"status": "error", "detail": f"Error processing error response: {str(e)}"}

            # 成功响应，尝试解析JSON
            try:
                # 直接返回原始API响应，不添加任何额外字段
                return response.json()
            except ValueError:
                # 如果不是有效的JSON，返回文本内容
                return {"status": "success", "data": response.text}
        except Exception as e:
            import traceback

            return {"status": "error", "detail": f"Error processing response: {str(e)}", "traceback": traceback.format_exc()}

    def is_docker_running(self):
        """Check if Docker is running."""
        endpoint = "is-docker-running"
        return self.get(endpoint)["is_docker_running"]

    def pull_image(self, image_name: str):
        """Pull a Docker image."""
        endpoint = "pull-image"
        return self.post(endpoint, payload={"image_name": image_name})

    def list_available_images(self, image_name: str):
        """List available images by name."""
        endpoint = f"available-images/{image_name}"
        return self.get(endpoint)

    def list_active_containers(self):
        """List all active containers."""
        endpoint = "active-containers"
        return self.get(endpoint)

    def list_exited_containers(self):
        """List all exited containers."""
        endpoint = "exited-containers"
        return self.get(endpoint)

    def clean_exited_containers(self):
        """Clean up exited containers."""
        endpoint = "clean-exited-containers"
        return self.post(endpoint, payload=None)

    def remove_container(self, container_name: str, archive_locally: bool = True, s3_bucket: str = None):
        """Remove a specific container."""
        endpoint = f"remove-container/{container_name}"
        params = {"archive_locally": archive_locally}
        if s3_bucket:
            params["s3_bucket"] = s3_bucket
        return self.post(endpoint, params=params)

    def stop_container(self, container_name: str):
        """Stop a specific container."""
        endpoint = f"stop-container/{container_name}"
        response = self.post(endpoint)

        # 特殊处理停止容器的响应
        if response is None or (isinstance(response, dict) and response.get("status") == "pending"):
            # 如果响应为None或pending，尝试查询容器状态
            time.sleep(2)  # 等待2秒，让操作有时间处理
            active_containers = self.list_active_containers()

            if isinstance(active_containers, dict) and "active_instances" in active_containers:
                # 检查容器是否不在活动容器列表中(已被停止)
                container_found = False
                for container in active_containers.get("active_instances", []):
                    if container.get("name") == container_name:
                        container_found = True
                        break

                if not container_found:
                    return {"status": "success", "message": f"容器 {container_name} 已停止", "code": 200}

            # 找不到明确状态时返回pending
            return {"status": "pending", "message": f"容器 {container_name} 停止请求已提交，但当前状态未知", "code": 202}

        return response

    def start_container(self, container_name: str):
        """Start a specific container."""
        endpoint = f"start-container/{container_name}"
        response = self.post(endpoint)

        # 特殊处理启动容器的响应
        if response is None or (isinstance(response, dict) and response.get("status") == "pending"):
            # 如果响应为None或pending，尝试查询容器状态
            time.sleep(2)  # 等待2秒，让操作有时间处理
            active_containers = self.list_active_containers()

            if isinstance(active_containers, dict) and "active_instances" in active_containers:
                # 检查容器是否在活动容器列表中
                for container in active_containers.get("active_instances", []):
                    if container.get("name") == container_name:
                        return {"status": "success", "message": f"容器 {container_name} 已启动", "code": 200}

            # 找不到容器时返回pending状态
            return {"status": "pending", "message": f"容器 {container_name} 启动请求已提交，但当前状态未知", "code": 202}

        return response

    def create_hummingbot_instance(self, instance_config: dict):
        """Create a new Hummingbot instance."""
        endpoint = "create-hummingbot-instance"
        return self.post(endpoint, payload=instance_config)

    def start_bot(self, start_bot_config: dict):
        """Start a Hummingbot bot."""
        endpoint = "start-bot"
        return self.post(endpoint, payload=start_bot_config)

    def stop_bot(self, bot_name: str, skip_order_cancellation: bool = False, async_backend: bool = False):
        """Stop a Hummingbot bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = "stop-bot"

        # 准备请求负载
        payload = {"bot_name": bot_name, "skip_order_cancellation": skip_order_cancellation, "async_backend": async_backend}

        # 打印实际发送的请求内容，帮助调试
        try:
            import logging

            logging.info(f"Stopping bot with payload: {payload}")
        except Exception:
            pass

        # 发送请求并记录响应
        try:
            response = self.post(endpoint, payload=payload)
            import logging

            logging.info(f"Stop bot response: {response}")
            return response
        except Exception as e:
            import logging

            logging.error(f"Stop bot request failed: {str(e)}")
            return {"status": "error", "message": f"停止机器人失败: {str(e)}"}

    def import_strategy(self, strategy_config: dict):
        """Import a trading strategy to a bot."""
        endpoint = "import-strategy"
        return self.post(endpoint, payload=strategy_config)

    def _extract_bot_name(self, bot_name: str) -> str:
        """
        从容器名称中提取API所需的bot_name部分
        例如从 'hummingbot-test_bot-2025.04.07_14.24' 提取 'test_bot'
        """
        # 保存原始名称用于调试
        original_name = bot_name

        # 添加调试输出到控制台
        # print(f"[DEBUG] 原始容器名称: '{original_name}', 不做提取，直接返回原名")

        # 直接返回原始容器名称，不再尝试提取
        return original_name

    def get_bot_status(self, bot_name: str):
        """Get the status of a bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = f"get-bot-status/{bot_name}"
        return self.get(endpoint)

    def get_bot_history(self, bot_name: str):
        """Get the historical data of a bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = f"get-bot-history/{bot_name}"
        return self.get(endpoint)

    def get_active_bots_status(self):
        """
        Retrieve the cached status of all active bots.
        Returns a JSON response with the status and data of active bots.
        """
        endpoint = "get-active-bots-status"
        return self.get(endpoint)

    def get_all_controllers_config(self):
        """Get all controller configurations."""
        endpoint = "all-controller-configs"
        return self.get(endpoint)

    def get_available_images(self, image_name: str = "hummingbot"):
        """Get available images."""
        endpoint = f"available-images/{image_name}"
        return self.get(endpoint)["available_images"]

    def add_script_config(self, script_config: dict):
        """Add a new script configuration."""
        endpoint = "add-script-config"
        return self.post(endpoint, payload=script_config)

    def add_controller_config(self, controller_config: dict):
        """Add a new controller configuration."""
        endpoint = "add-controller-config"
        config = {"name": controller_config["id"], "content": controller_config}
        return self.post(endpoint, payload=config)

    def delete_controller_config(self, controller_name: str):
        """Delete a controller configuration."""
        url = "delete-controller-config"
        return self.post(url, params={"config_name": controller_name})

    def delete_script_config(self, script_name: str):
        """Delete a script configuration."""
        url = "delete-script-config"
        return self.post(url, params={"script_name": script_name})

    def delete_all_controller_configs(self):
        """Delete all controller configurations."""
        endpoint = "delete-all-controller-configs"
        return self.post(endpoint)

    def delete_all_script_configs(self):
        """Delete all script configurations."""
        endpoint = "delete-all-script-configs"
        return self.post(endpoint)

    def get_real_time_candles(self, connector: str, trading_pair: str, interval: str, max_records: int):
        """Get candles data."""
        endpoint = "real-time-candles"
        payload = {"connector": connector, "trading_pair": trading_pair, "interval": interval, "max_records": max_records}
        return self.post(endpoint, payload=payload)

    def get_historical_candles(self, connector: str, trading_pair: str, interval: str, start_time: int, end_time: int):
        """Get historical candles data."""
        endpoint = "historical-candles"
        payload = {
            "connector_name": connector,
            "trading_pair": trading_pair,
            "interval": interval,
            "start_time": start_time,
            "end_time": end_time,
        }
        return self.post(endpoint, payload=payload)

    def run_backtesting(self, start_time: int, end_time: int, backtesting_resolution: str, trade_cost: float, config: dict):
        """Run backtesting."""
        endpoint = "run-backtesting"
        payload = {
            "start_time": start_time,
            "end_time": end_time,
            "backtesting_resolution": backtesting_resolution,
            "trade_cost": trade_cost,
            "config": config,
        }
        backtesting_results = self.post(endpoint, payload=payload)
        if "error" in backtesting_results:
            raise Exception(backtesting_results["error"])
        if "processed_data" not in backtesting_results:
            data = None
        else:
            data = pd.DataFrame(backtesting_results["processed_data"])
        if "executors" not in backtesting_results:
            executors = []
        else:
            executors = [ExecutorInfo(**executor) for executor in backtesting_results["executors"]]
        return {"processed_data": data, "executors": executors, "results": backtesting_results["results"]}

    def get_all_configs_from_bot(self, bot_name: str):
        """Get all configurations from a bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = f"all-controller-configs/bot/{bot_name}"
        return self.get(endpoint)

    def stop_controller_from_bot(self, bot_name: str, controller_id: str):
        """Stop a controller from a bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = f"update-controller-config/bot/{bot_name}/{controller_id}"
        config = {"manual_kill_switch": True}
        return self.post(endpoint, payload=config)

    def start_controller_from_bot(self, bot_name: str, controller_id: str):
        """Start a controller from a bot."""
        bot_name = self._extract_bot_name(bot_name)
        endpoint = f"update-controller-config/bot/{bot_name}/{controller_id}"
        config = {"manual_kill_switch": False}
        return self.post(endpoint, payload=config)

    def get_connector_config_map(self, connector_name: str):
        """Get connector configuration map."""
        endpoint = f"connector-config-map/{connector_name}"
        return self.get(endpoint)

    def get_all_connectors_config_map(self):
        """Get all connector configuration maps."""
        endpoint = "all-connectors-config-map"
        return self.get(endpoint)

    def add_account(self, account_name: str):
        """Add a new account."""
        endpoint = "add-account"
        return self.post(endpoint, params={"account_name": account_name})

    def delete_account(self, account_name: str):
        """Delete an account."""
        endpoint = "delete-account"
        return self.post(endpoint, params={"account_name": account_name})

    def delete_credential(self, account_name: str, connector_name: str):
        """Delete credentials."""
        endpoint = f"delete-credential/{account_name}/{connector_name}"
        return self.post(endpoint)

    def add_connector_keys(self, account_name: str, connector_name: str, connector_config: dict):
        """Add connector keys."""
        endpoint = f"add-connector-keys/{account_name}/{connector_name}"
        return self.post(endpoint, payload=connector_config)

    def get_accounts(self):
        """Get available credentials."""
        endpoint = "list-accounts"
        return self.get(endpoint)

    def get_credentials(self, account_name: str):
        """Get available credentials."""
        endpoint = f"list-credentials/{account_name}"
        return self.get(endpoint)

    def get_accounts_state(self):
        """Get all balances."""
        endpoint = "accounts-state"
        return self.get(endpoint)

    def get_account_state_history(self):
        """Get account state history."""
        endpoint = "account-state-history"
        return self.get(endpoint)

    def get_performance_results(self, executors: List[Dict[str, Any]]):
        if not isinstance(executors, list) or len(executors) == 0:
            raise ValueError("Executors must be a non-empty list of dictionaries")
        # Check if all elements in executors are dictionaries
        if not all(isinstance(executor, dict) for executor in executors):
            raise ValueError("All elements in executors must be dictionaries")
        endpoint = "get-performance-results"
        payload = {
            "executors": executors,
        }

        performance_results = self.post(endpoint, payload=payload)
        if "error" in performance_results:
            raise Exception(performance_results["error"])
        if "detail" in performance_results:
            raise Exception(performance_results["detail"])
        if "processed_data" not in performance_results:
            data = None
        else:
            data = pd.DataFrame(performance_results["processed_data"])
        if "executors" not in performance_results:
            executors = []
        else:
            executors = [ExecutorInfo(**executor) for executor in performance_results["executors"]]
        return {"processed_data": data, "executors": executors, "results": performance_results["results"]}

    def list_databases(self):
        """Get databases list."""
        endpoint = "list-databases"
        return self.post(endpoint)

    def read_databases(self, db_paths: List[str]):
        """Read databases."""
        endpoint = "read-databases"
        response = self.post(endpoint, payload=db_paths)

        # 添加表名大小写适配逻辑
        if isinstance(response, list):
            for db in response:
                # 通用处理任意表名的大小写问题
                self._normalize_table_case(db)

                # 确保数值型字段使用正确的数据类型，避免cumsum错误
                if "executors" in db and isinstance(db["executors"], list):
                    numeric_columns = ["net_pnl_pct", "net_pnl_quote", "cum_fees_quote", "filled_amount_quote"]
                    for record in db["executors"]:
                        for col in numeric_columns:
                            if col in record and record[col] is not None:
                                try:
                                    record[col] = float(record[col])
                                except (ValueError, TypeError):
                                    record[col] = 0.0

        return response

    def create_checkpoint(self, db_names: List[str]):
        """Create a checkpoint."""
        endpoint = "create-checkpoint"
        return self.post(endpoint, payload=db_names)

    def list_checkpoints(self, full_path: bool):
        """List checkpoints."""
        endpoint = "list-checkpoints"
        params = {"full_path": full_path}
        return self.post(endpoint, params=params)

    def load_checkpoint(self, checkpoint_path: str):
        """Load a checkpoint."""
        endpoint = "load-checkpoint"
        params = {"checkpoint_path": checkpoint_path}
        response = self.post(endpoint, params=params)

        # 添加表名大小写适配逻辑
        if isinstance(response, dict):
            # 通用处理任意表名的大小写问题
            self._normalize_table_case(response)

            # 确保数值型字段使用正确的数据类型
            if "executors" in response and isinstance(response["executors"], list):
                numeric_columns = ["net_pnl_pct", "net_pnl_quote", "cum_fees_quote", "filled_amount_quote"]
                for record in response["executors"]:
                    for col in numeric_columns:
                        if col in record and record[col] is not None:
                            try:
                                record[col] = float(record[col])
                            except (ValueError, TypeError):
                                record[col] = 0.0

        return response

    def _normalize_table_case(self, data: Dict[str, Any]):
        """通用处理数据库表名的大小写问题"""
        if not isinstance(data, dict):
            return

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
