# API端点列表，基于OpenAPI文档
ENDPOINTS = [
    # Docker管理
    {"端点": "is-docker-running", "方法": "GET", "描述": "检查Docker是否正在运行", "参数": "无"},
    {
        "端点": "available-images/{image_name}",
        "方法": "GET",
        "描述": "获取指定镜像的可用版本",
        "参数": "路径参数: image_name",
    },
    {"端点": "active-containers", "方法": "GET", "描述": "获取正在运行的容器列表", "参数": "无"},
    {"端点": "exited-containers", "方法": "GET", "描述": "获取已停止的容器列表", "参数": "无"},
    {"端点": "clean-exited-containers", "方法": "POST", "描述": "清理已停止的容器", "参数": "无"},
    {
        "端点": "remove-container/{container_name}",
        "方法": "POST",
        "描述": "删除指定的容器",
        "参数": "路径参数: container_name, 查询参数: archive_locally=true, s3_bucket",
    },
    {
        "端点": "stop-container/{container_name}",
        "方法": "POST",
        "描述": "停止指定的容器",
        "参数": "路径参数: container_name",
    },
    {
        "端点": "start-container/{container_name}",
        "方法": "POST",
        "描述": "启动指定的容器",
        "参数": "路径参数: container_name",
    },
    {
        "端点": "create-hummingbot-instance",
        "方法": "POST",
        "描述": "创建新的Hummingbot实例",
        "参数": '{"instance_name": "实例名称", "credentials_profile": "凭证配置", "image": "hummingbot/hummingbot:latest", "script": "脚本名称", "script_config": "脚本配置"}',
    },
    {"端点": "pull-image/", "方法": "POST", "描述": "拉取Docker镜像", "参数": '{"image_name": "镜像名称:标签"}'},
    # 机器人管理
    {"端点": "get-active-bots-status", "方法": "GET", "描述": "获取活跃机器人状态", "参数": "无"},
    {
        "端点": "get-bot-status/{bot_name}",
        "方法": "GET",
        "描述": "获取指定机器人的状态",
        "参数": "路径参数: bot_name",
    },
    {
        "端点": "get-bot-history/{bot_name}",
        "方法": "GET",
        "描述": "获取指定机器人的历史",
        "参数": "路径参数: bot_name",
    },
    {
        "端点": "start-bot",
        "方法": "POST",
        "描述": "启动Hummingbot实例",
        "参数": '{"bot_name": "实例名称", "log_level": "日志级别", "script": "脚本名称", "conf": "配置名称", "async_backend": false}',
    },
    {
        "端点": "stop-bot",
        "方法": "POST",
        "描述": "停止Hummingbot实例",
        "参数": '{"bot_name": "实例名称", "skip_order_cancellation": false, "async_backend": false}',
    },
    {
        "端点": "import-strategy",
        "方法": "POST",
        "描述": "导入交易策略",
        "参数": '{"bot_name": "实例名称", "strategy": "策略名称"}',
    },
    # 文件管理
    {"端点": "list-scripts", "方法": "GET", "描述": "获取可用脚本列表", "参数": "无"},
    {"端点": "list-scripts-configs", "方法": "GET", "描述": "获取可用脚本配置列表", "参数": "无"},
    {
        "端点": "script-config/{script_name}",
        "方法": "GET",
        "描述": "获取指定脚本的配置",
        "参数": "路径参数: script_name",
    },
    {"端点": "list-controllers", "方法": "GET", "描述": "获取控制器列表", "参数": "无"},
    {"端点": "list-controllers-configs", "方法": "GET", "描述": "获取控制器配置列表", "参数": "无"},
    {
        "端点": "controller-config/{controller_name}",
        "方法": "GET",
        "描述": "获取指定控制器的配置",
        "参数": "路径参数: controller_name",
    },
    {"端点": "all-controller-configs", "方法": "GET", "描述": "获取所有控制器配置", "参数": "无"},
    {
        "端点": "all-controller-configs/bot/{bot_name}",
        "方法": "GET",
        "描述": "获取指定机器人的所有控制器配置",
        "参数": "路径参数: bot_name",
    },
    {
        "端点": "update-controller-config/bot/{bot_name}/{controller_id}",
        "方法": "POST",
        "描述": "更新控制器配置",
        "参数": "路径参数: bot_name, controller_id, 请求体: {config对象}",
    },
    {
        "端点": "add-script",
        "方法": "POST",
        "描述": "添加脚本",
        "参数": '{"name": "脚本名称", "content": "脚本内容"}',
    },
    {
        "端点": "upload-script",
        "方法": "POST",
        "描述": "上传脚本文件",
        "参数": "表单: config_file, 查询参数: override=false",
    },
    {
        "端点": "add-script-config",
        "方法": "POST",
        "描述": "添加脚本配置",
        "参数": '{"name": "配置名称", "content": {配置对象}}',
    },
    {
        "端点": "upload-script-config",
        "方法": "POST",
        "描述": "上传脚本配置文件",
        "参数": "表单: config_file, 查询参数: override=false",
    },
    {
        "端点": "add-controller-config",
        "方法": "POST",
        "描述": "添加控制器配置",
        "参数": '{"name": "配置名称", "content": {配置对象}}',
    },
    {
        "端点": "upload-controller-config",
        "方法": "POST",
        "描述": "上传控制器配置文件",
        "参数": "表单: config_file, 查询参数: override=false",
    },
    {
        "端点": "delete-controller-config",
        "方法": "POST",
        "描述": "删除控制器配置",
        "参数": "查询参数: config_name",
    },
    {"端点": "delete-script-config", "方法": "POST", "描述": "删除脚本配置", "参数": "查询参数: config_name"},
    {"端点": "delete-all-controller-configs", "方法": "POST", "描述": "删除所有控制器配置", "参数": "无"},
    {"端点": "delete-all-script-configs", "方法": "POST", "描述": "删除所有脚本配置", "参数": "无"},
    # 市场数据
    {
        "端点": "real-time-candles",
        "方法": "POST",
        "描述": "获取实时K线数据",
        "参数": '{"connector": "连接器名称", "trading_pair": "交易对", "interval": "1m", "max_records": 500}',
    },
    {
        "端点": "historical-candles",
        "方法": "POST",
        "描述": "获取历史K线数据",
        "参数": '{"connector_name": "binance_perpetual", "trading_pair": "BTC-USDT", "interval": "3m", "start_time": 1672542000, "end_time": 1672628400}',
    },
    # 回测
    {
        "端点": "run-backtesting",
        "方法": "POST",
        "描述": "运行回测",
        "参数": '{"start_time": 1672542000, "end_time": 1672628400, "backtesting_resolution": "1m", "trade_cost": 0.0006, "config": {配置对象}}',
    },
    # 数据库管理
    {"端点": "list-databases", "方法": "POST", "描述": "列出数据库", "参数": "无"},
    {"端点": "read-databases", "方法": "POST", "描述": "读取数据库", "参数": '["数据库路径1", "数据库路径2"]'},
    {"端点": "create-checkpoint", "方法": "POST", "描述": "创建检查点", "参数": '["数据库路径1", "数据库路径2"]'},
    {"端点": "list-checkpoints", "方法": "POST", "描述": "列出检查点", "参数": "查询参数: full_path=true"},
    {"端点": "load-checkpoint", "方法": "POST", "描述": "加载检查点", "参数": "查询参数: checkpoint_path"},
    # 性能
    {"端点": "get-performance-results", "方法": "POST", "描述": "获取性能结果", "参数": "请求体: {配置对象}"},
    # 凭证管理
    {"端点": "accounts-state", "方法": "GET", "描述": "获取所有账户状态", "参数": "无"},
    {"端点": "account-state-history", "方法": "GET", "描述": "获取账户状态历史", "参数": "无"},
    {"端点": "available-connectors", "方法": "GET", "描述": "获取可用连接器列表", "参数": "无"},
    {
        "端点": "connector-config-map/{connector_name}",
        "方法": "GET",
        "描述": "获取连接器配置映射",
        "参数": "路径参数: connector_name",
    },
    {"端点": "all-connectors-config-map", "方法": "GET", "描述": "获取所有连接器配置映射", "参数": "无"},
    {"端点": "list-accounts", "方法": "GET", "描述": "列出账户", "参数": "无"},
    {
        "端点": "list-credentials/{account_name}",
        "方法": "GET",
        "描述": "列出指定账户的凭证",
        "参数": "路径参数: account_name",
    },
    {"端点": "add-account", "方法": "POST", "描述": "添加账户", "参数": "查询参数: account_name"},
    {"端点": "delete-account", "方法": "POST", "描述": "删除账户", "参数": "查询参数: account_name"},
    {
        "端点": "delete-credential/{account_name}/{connector_name}",
        "方法": "POST",
        "描述": "删除凭证",
        "参数": "路径参数: account_name, connector_name",
    },
    {
        "端点": "add-connector-keys/{account_name}/{connector_name}",
        "方法": "POST",
        "描述": "添加连接器密钥",
        "参数": "路径参数: account_name, connector_name, 请求体: {keys对象}",
    },
]
