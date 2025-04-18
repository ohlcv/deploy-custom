# 现货永续套利策略配置工具

欢迎使用现货永续套利策略配置工具！本工具允许您创建、修改、可视化和保存现货永续套利策略的配置。该策略通过现货和永续市场之间的价格差异获利。

## 功能特点

- **跨市场交易**: 在现货和永续市场之间交易
- **价差监控**: 跟踪和可视化价格差异
- **动态仓位管理**: 灵活的仓位大小和风险管理
- **可视化配置**: 直观查看价格走势和价差
- **保存部署**: 保存配置以供后续部署

## 使用方法

### 1. 基本配置

首先配置基本参数：
- **现货交易所**: 选择您偏好的现货交易所
- **永续交易所**: 选择您偏好的永续合约交易所
- **交易对**: 选择加密货币交易对（例如："BTC-USDT"）
- **持仓模式**: 选择 HEDGE（对冲）或 ONEWAY（单向）模式
- **杠杆**: 设置永续合约交易的杠杆率

### 2. 图表配置

配置市场数据的可视化方式：
- **时间间隔**: 选择K线时间框架（1分钟到1天）
- **显示天数**: 选择显示历史数据的天数

### 3. 策略参数

精细调整策略参数：

a. **订单配置**:
- **总计价币数量**: 用于交易的计价币总量
- **最小价差百分比**: 触发交易的最小价格差异百分比

b. **高级参数**:
- **最小交易量**: 基础货币的最小交易量
- **最大交易量**: 基础货币的最大交易量
- **最大仓位大小**: 最大总仓位大小
- **冷却时间**: 交易之间的最小间隔时间

c. **市场参数**:
- **现货市场滑点**: 现货订单允许的最大滑点
- **永续市场滑点**: 永续订单允许的最大滑点

## 理解现货永续套利

现货永续套利策略通过现货和永续市场之间的价格差异获利。以下是其工作原理：

### 基本概念
- 监控市场间价格差异
- 在出现盈利机会时开仓
- 等待价格差异收敛时平仓
- 通过仓位限制和滑点控制管理风险

### 策略机制
- 当永续价格 > 现货价格 + 阈值时：
  1. 在现货市场买入
  2. 在永续市场卖出
  3. 等待价格收敛
  4. 平仓获利

- 当现货价格 > 永续价格 + 阈值时：
  1. 在现货市场卖出
  2. 在永续市场买入
  3. 等待价格收敛
  4. 平仓获利

### 风险管理
- 仓位大小限制
- 市场滑点控制
- 交易间冷却期
- 最大仓位上限

## 最佳实践

1. **市场选择**
   - 选择流动性好的市场
   - 监控价格相关性
   - 考虑交易所费用
   - 关注市场无效性

2. **仓位管理**
   - 从保守的仓位大小开始
   - 平衡仓位比例
   - 监控价格收敛
   - 跟踪总体风险敞口

3. **风险控制**
   - 设置适当的滑点限制
   - 使用合理的杠杆
   - 维持充足的保证金
   - 考虑市场条件

4. **性能优化**
   - 跟踪盈亏情况
   - 监控执行成本
   - 分析交易分布
   - 根据结果调整参数

## 技术细节

### 入场条件
```
做多现货/做空永续：
永续价格 > 现货价格 * (1 + 最小价差百分比)

做空现货/做多永续：
现货价格 > 永续价格 * (1 + 最小价差百分比)
```

### 仓位计算
```
仓位大小 = min(
    max(
        计价币数量 / 当前价格,
        最小交易量
    ),
    最大交易量
)
```

### 盈利计算
```
盈利 = 价格差异 * 仓位大小 - 交易费用
```

## 故障排除

1. **无法开仓**
   - 检查价格差异是否达到最小阈值
   - 验证余额和杠杆是否充足
   - 检查市场流动性
   - 确认交易所连接状态

2. **意外亏损**
   - 检查市场滑点设置
   - 检查仓位大小
   - 分析市场走势
   - 监控价格收敛情况

3. **策略表现**
   - 跟踪价差模式
   - 监控执行成本
   - 分析市场条件
   - 根据需要调整参数

## 支持

如需额外支持：
- 查看文档
- 加入社区论坛
- 联系技术支持 