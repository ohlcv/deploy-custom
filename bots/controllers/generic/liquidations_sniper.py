import time
from decimal import Decimal
from typing import Dict, List, Set

from pydantic import Field, validator

from hummingbot.client.config.config_data_types import ClientFieldData
from hummingbot.core.data_type.common import PositionMode, PriceType, TradeType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.data_feed.liquidations_feed.liquidations_base import LiquidationSide
from hummingbot.data_feed.liquidations_feed.liquidations_factory import (
    LiquidationsConfig,
    LiquidationsFactory,
)
from hummingbot.strategy_v2.controllers.controller_base import (
    ControllerBase,
    ControllerConfigBase,
)
from hummingbot.strategy_v2.executors.dca_executor.data_types import (
    DCAExecutorConfig,
    DCAMode,
)
from hummingbot.strategy_v2.models.executor_actions import (
    CreateExecutorAction,
    ExecutorAction,
)


class LiquidationSniperConfig(ControllerConfigBase):
    """
    This controller executes a strategy that listens for liquidations on Binance for the given pair
    and executes a DCA trade to profit from the rebound. The profitability is highly dependent on the
    settings you make.

    Docs: https://www.notion.so/hummingbot-foundation/Liquidation-Sniper-V2-Framework-739dadb04eac4aa6a082067e06ddf7db
    """

    # 中文注释: 清算狙击手配置类，用于执行监听币安清算事件并通过DCA交易从反弹中获利的策略
    # 策略盈利能力高度依赖于您的设置参数

    controller_name: str = "liquidations_sniper"
    controller_type: str = "generic"
    candles_config: List[CandlesConfig] = []  # do not need any candles for that
    # 中文注释: 不需要任何K线数据

    # ---------------------------------------------------------------------------------------
    # Liquidations Config
    # 中文注释: 清算配置
    # ---------------------------------------------------------------------------------------

    connector_name: str = Field(
        default="kucoin_perpetual",
        client_data=ClientFieldData(
            prompt=lambda msg: "Enter the trading connector (where the execution of the order shall take place): ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 交易连接器，即执行订单的交易所

    trading_pair: str = Field(
        default="XBT-USDT",
        client_data=ClientFieldData(
            prompt=lambda msg: "Enter the trading pair which you want to use for trading: ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 用于交易的交易对

    liquidation_side: LiquidationSide = Field(
        default="LONG",
        client_data=ClientFieldData(
            prompt=lambda msg: "Enter which liquidations you want to trade on (SHORT/LONG). Trading long liquidations "
            "means price is going down and over-leveraged long positions get forcefully liquidated. "
            "The strategy would then DCA-Buy into that liquidation and waiting for the rebound: ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 要交易的清算方向(SHORT/LONG)
    # 交易多头清算意味着价格下跌，高杠杆多头头寸被强制清算
    # 策略会DCA买入并等待价格反弹

    liquidations_pair: str = Field(
        default="BTC-USDT",
        client_data=ClientFieldData(
            prompt=lambda msg: "Enter the liquidations pair to monitor on Binance: ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 在币安监控清算事件的交易对

    liquidations_interval_seconds: int = Field(
        default=15,
        client_data=ClientFieldData(
            prompt=lambda msg: "The amount of seconds to accumulate liquidations (e.g. if more than 10Mio USDT "
            "[=liquidations_trigger_usd_amount] is liquidated in 15s, then place the orders): ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 累积清算事件的时间间隔(秒)
    # 例如，如果在15秒内有超过1000万USDT的清算，则下单

    liquidations_trigger_usd_amount: int = Field(
        default=10_000_000,  # 10 Mio USDT
        client_data=ClientFieldData(
            is_updatable=True,
            prompt=lambda msg: "The amount of USD that was liquidated in the liquidations-interval to "
            "actually place the trade: ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 触发交易的美元清算金额阈值，默认为1000万USDT

    # ---------------------------------------------------------------------------------------
    # DCA Config
    # 中文注释: DCA(分批买入)配置
    # ---------------------------------------------------------------------------------------

    total_amount_quote: Decimal = Field(
        default=100,
        client_data=ClientFieldData(
            is_updatable=True,
            prompt_on_new=True,
            prompt=lambda mi: "Enter the total amount in quote asset to use for trading (e.g., 100):",
        ),
    )
    # 中文注释: 用于交易的计价资产总额，例如100USDT

    dca_levels_percent: List[Decimal] = Field(
        default="0.01,0.02,0.03,0.05",
        client_data=ClientFieldData(
            prompt_on_new=True,
            is_updatable=True,
            prompt=lambda msg: "Enter a comma-separated list of percentage values where each DCA level should be "
            "placed (as a decimal, e.g., 0.01 for 1%): ",
        ),
    )
    # 中文注释: 各DCA级别的百分比位置(逗号分隔)
    # 例如，0.01表示从触发价格下降/上升1%的位置

    dca_amounts_percent: List[Decimal] = Field(
        default="0.1,0.2,0.3,0.4",
        client_data=ClientFieldData(
            prompt_on_new=True,
            is_updatable=True,
            prompt=lambda msg: "Enter a comma-separated list of percentage values of the total quote amount that "
            "should be placed at each DCA level (as a decimal, e.g., 0.1 for 10%): ",
        ),
    )
    # 中文注释: 分配给各DCA级别的总金额百分比(逗号分隔)
    # 例如，0.1表示将总额的10%分配给该级别

    stop_loss: Decimal = Field(
        default=Decimal("0.03"),
        gt=0,
        client_data=ClientFieldData(
            is_updatable=True,
            prompt=lambda msg: "Enter the stop loss (as a decimal, e.g., 0.03 for 3%): ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 止损百分比，默认为3%

    take_profit: Decimal = Field(
        default=Decimal("0.01"),
        gte=0,
        client_data=ClientFieldData(
            is_updatable=True,
            prompt=lambda msg: "Enter the take profit (as a decimal, e.g., 0.01 for 1%): ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 止盈百分比，默认为1%

    time_limit: int = Field(
        default=60 * 30,
        gt=0,
        client_data=ClientFieldData(
            is_updatable=True,
            prompt=lambda msg: "Enter the time limit in seconds (e.g., 1800 for 30 minutes): ",
            prompt_on_new=True,
        ),
    )
    # 中文注释: 交易时间限制(秒)，默认为30分钟(1800秒)

    # ---------------------------------------------------------------------------------------
    # Perp Config
    # 中文注释: 永续合约配置
    # ---------------------------------------------------------------------------------------

    leverage: int = Field(
        default=5,
        client_data=ClientFieldData(
            prompt_on_new=True,
            prompt=lambda msg: "Set the leverage to use for trading (e.g., 5 for 5x leverage). "
            "Set it to 1 for spot trading:",
        ),
    )
    # 中文注释: 交易杠杆，默认为5倍。现货交易请设为1

    position_mode: PositionMode = Field(
        default="HEDGE",
        client_data=ClientFieldData(
            prompt=lambda msg: "Enter the position mode (HEDGE/ONEWAY): ",
            prompt_on_new=False,
        ),
    )
    # 中文注释: 仓位模式(HEDGE对冲/ONEWAY单向)，默认为对冲模式

    # ---------------------------------------------------------------------------------------
    # Validators
    # 中文注释: 验证器
    # ---------------------------------------------------------------------------------------

    @validator("liquidations_pair", pre=True, always=True)
    def validate_usdm_pair(cls, value):
        # 中文注释: 验证清算交易对是否为USDT计价的合约
        if "usd" in value.lower():
            return value
        raise ValueError("Liquidations pair must be a USDⓈ-M Future contract!")

    @validator("time_limit", "stop_loss", "take_profit", pre=True, always=True)
    def validate_target(cls, value):
        # 中文注释: 验证时间限制、止损和止盈的值
        if isinstance(value, str):
            if value == "":
                return None
            return Decimal(value)
        return value

    @validator("dca_levels_percent", pre=True, always=True)
    def parse_levels(cls, value) -> List[Decimal]:
        # 中文注释: 解析DCA级别百分比
        if value is None:
            return []
        if isinstance(value, str):
            if value == "":
                return []
            return [Decimal(x.strip()) for x in value.split(",")]
        return value

    @validator("dca_amounts_percent", pre=True, always=True)
    def parse_and_validate_amounts(cls, value, values, field) -> List[Decimal]:
        # 中文注释: 解析和验证DCA金额百分比，确保与级别数量匹配
        if value is None or value == "":
            return [Decimal(1) for _ in values[values["dca_levels_percent"]]]
        if isinstance(value, str):
            return [Decimal(x.strip()) for x in value.split(",")]
        elif isinstance(value, list) and len(value) != len(
            values["dca_levels_percent"]
        ):
            raise ValueError(
                f"The number of {field.name} must match the number of levels ({len(values['dca_levels_percent'])})."
            )
        elif isinstance(value, list):
            return [Decimal(amount) for amount in value]
        raise ValueError("DCA amounts per level is invalid!")

    @validator("position_mode", pre=True, allow_reuse=True)
    def validate_position_mode(cls, value: str) -> PositionMode:
        # 中文注释: 验证仓位模式是否有效
        if isinstance(value, str) and value.upper() in PositionMode.__members__:
            return PositionMode[value.upper()]
        raise ValueError(
            f"Invalid position mode: {value}. Valid options are: {', '.join(PositionMode.__members__)}"
        )

    @validator("liquidation_side", pre=True, always=True)
    def validate_liquidation_side(cls, value: str) -> LiquidationSide:
        # 中文注释: 验证清算方向是否有效
        if isinstance(value, str) and value.upper() in LiquidationSide.__members__:
            return LiquidationSide[value.upper()]
        raise ValueError(
            f"Invalid liquidation side: {value}. Valid options are: {', '.join(LiquidationSide.__members__)}"
        )

    # ---------------------------------------------------------------------------------------
    # Market Config
    # 中文注释: 市场配置
    # ---------------------------------------------------------------------------------------

    def update_markets(self, markets: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        # 中文注释: 更新市场列表，添加当前策略使用的交易对
        if self.connector_name not in markets:
            markets[self.connector_name] = set()
        markets[self.connector_name].add(self.trading_pair)
        return markets


class LiquidationSniper(ControllerBase):
    # 中文注释: 清算狙击手策略控制器类，实现了策略的核心逻辑

    def __init__(self, config: LiquidationSniperConfig, *args, **kwargs):
        # 中文注释: 初始化控制器，设置配置和清算数据源
        super().__init__(config, *args, **kwargs)
        self.config = config  # only for type check in IDE
        self.liquidations_feed = None
        self.initialize_liquidations_feed()
        # Make the configuration more forgiving, by calculating the real percentages if not done already
        # 中文注释: 通过计算实际百分比使配置更加灵活
        self.dca_amounts_pct = [
            Decimal(amount) / sum(self.config.dca_amounts_percent)
            for amount in self.config.dca_amounts_percent
        ]

    def initialize_liquidations_feed(self):
        # 中文注释: 初始化清算数据源，从币安获取清算事件数据
        liquidations_config = LiquidationsConfig(
            connector="binance",  # use Binance as the most liquid exchange (currently the only feed supported!)
            max_retention_seconds=self.config.liquidations_interval_seconds,
            trading_pairs=[self.config.liquidations_pair],
        )
        self.liquidations_feed = LiquidationsFactory.get_liquidations_feed(
            liquidations_config
        )

    def on_start(self):
        # 中文注释: 启动策略时执行，开始监控清算事件
        self.liquidations_feed.start()
        self.logger().info(
            "Watching for {} liquidations happening on {} (Binance) within {}s to exceed {} USD".format(
                self.config.liquidation_side,
                self.config.liquidations_pair,
                self.config.liquidations_interval_seconds,
                self.config.liquidations_trigger_usd_amount,
            )
        )

    def on_stop(self):
        # 中文注释: 停止策略时执行，停止清算数据源
        self.liquidations_feed.stop()

    async def update_processed_data(self):
        # 中文注释: 更新处理过的数据，计算清算美元总额
        df = self.liquidations_feed.liquidations_df(self.config.liquidations_pair)
        df["usd_amount"] = df["quantity"] * df["price"]
        df = df[df["side"] == self.config.liquidation_side]
        self.processed_data["liquidated_usd_amount"] = df["usd_amount"].sum()

    def determine_executor_actions(self) -> List[ExecutorAction]:
        # 中文注释: 确定执行器动作，当清算金额超过阈值且当前没有活跃交易时创建新的DCA执行器
        executor_actions = []
        liquidated_usd_amount = self.processed_data["liquidated_usd_amount"]
        trading_executors = self.filter_executors(
            executors=self.executors_info,
            filter_func=lambda executor: executor.is_active
            and executor.controller_id == self.config.id,
        )

        # Only initiate a trade when both criteria is met
        # 中文注释: 仅当满足两个条件时才启动交易：清算金额超过阈值且没有活跃的交易执行器
        if (
            liquidated_usd_amount >= self.config.liquidations_trigger_usd_amount
            and len(trading_executors) == 0
        ):
            self.logger().info(
                "The current liquidation-amount ({} USD) in the last {}s is above threshold "
                "of {} USD => entering trade!".format(
                    liquidated_usd_amount,
                    self.config.liquidations_interval_seconds,
                    self.config.liquidations_trigger_usd_amount,
                )
            )
            executor_actions.append(
                CreateExecutorAction(
                    executor_config=self.get_dca_executor_config(),
                    controller_id=self.config.id,
                )
            )
        return executor_actions

    def get_dca_executor_config(self) -> DCAExecutorConfig:
        # 中文注释: 获取DCA执行器配置，根据清算方向设置交易类型和价格
        trade_type = (
            TradeType.BUY
            if self.config.liquidation_side == LiquidationSide.LONG
            else TradeType.SELL
        )

        # Use the mid-price to calculate the levels, sl and tp
        # 中文注释: 使用中间价格计算各级别的价格、止损和止盈
        price = self.market_data_provider.get_price_by_type(
            self.config.connector_name, self.config.trading_pair, PriceType.MidPrice
        )
        if trade_type == TradeType.BUY:
            # 中文注释: 如果是买入，则在当前价格下方设置各级别价格
            prices = [price * (1 - level) for level in self.config.dca_levels_percent]
        else:
            # 中文注释: 如果是卖出，则在当前价格上方设置各级别价格
            prices = [price * (1 + level) for level in self.config.dca_levels_percent]

        # 中文注释: 计算每个级别的下单金额
        amounts_quote = [
            self.config.total_amount_quote * pct for pct in self.dca_amounts_pct
        ]

        # 中文注释: 返回DCA执行器配置
        return DCAExecutorConfig(
            controller_id=self.config.id,
            timestamp=time.time(),
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            mode=DCAMode.MAKER,  # 中文注释: 使用做市商模式
            leverage=self.config.leverage,
            side=trade_type,
            amounts_quote=amounts_quote,
            prices=prices,
            take_profit=self.config.take_profit,
            stop_loss=self.config.stop_loss,
            time_limit=self.config.time_limit,
        )

    def to_format_status(self) -> List[str]:
        # 中文注释: 格式化状态信息，显示当前清算金额
        return [
            "Currently liquidated {} of pair {} in the last {} seconds: {} USD".format(
                self.config.liquidation_side,
                self.config.liquidations_pair,
                self.config.liquidations_interval_seconds,
                self.processed_data["liquidated_usd_amount"],
            )
        ]
