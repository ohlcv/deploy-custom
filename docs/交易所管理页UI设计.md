以下是重新设计的交易所管理页面 UI 设计文档，根据您的需求进行了调整，确保既方便操作又美观简洁，充分利用账户 API 符合最佳实践，同时满足动态表单生成、交易所产品归类、CEX/DEX 区分、默认账户选择以及第一版显示部分交易所并保留扩展性的要求。我已完整阅读您上传的文档，并严格基于已有 API（如 `GET /available-connectors`、`GET /connector-config-map/{connector_name}` 等）进行设计。

---

# 交易所管理页面 UI 设计文档

## 1. 设计目标

### 1.1 功能目标
- **动态表单生成**：根据所选交易所和产品类型（如 `gate_io` 或 `gate_io_perpetual`），动态显示所需字段（如 `gate_io_api_key` 或 `gate_io_perpetual_user_id`）。
- **产品归类**：将同一交易所的不同产品（如 Gate.io 的现货和永续合约）归类显示。
- **CEX 与 DEX 区分**：明确区分中心化交易所（CEX）和去中心化交易所（DEX）。
- **默认账户**：默认选中列表中的第一个账户，便于用户直接操作。
- **配置驱动的交易所列表**：基于配置文件控制显示的交易所，方便后续扩展。
- **操作便捷**：支持添加、查看、修改、删除账户和连接器，提供筛选和分页功能。
- **美观简洁**：界面清晰，布局合理，视觉反馈明确。

### 1.2 适配性目标
- **API 合规**：使用账户 API 中已有的接口（如 `GET /available-connectors`、`POST /add-connector-keys/{account_name}/{connector_name}` 等）。
- **动态字段**：通过 `GET /connector-config-map/{connector_name}` 获取字段并动态生成表单。
- **扩展性**：通过 `config/exchangeConfig.ts` 配置文件控制显示的交易所，无需修改代码即可添加新交易所。

---

## 2. 页面布局与控件设计

### 2.1 整体布局
- **顶部区域**：筛选和操作控件。
- **中间区域**：账户列表表格，按 CEX 和 DEX 分组展示。
- **底部区域**：空状态显示（无数据时）。
- **弹窗**：用于添加、修改、查看密钥，添加账户，确认删除。

---

### 2.2 详细设计

#### 2.2.1 顶部区域
- **筛选控件**：
  - **账户名称下拉框**：
    - 显示所有账户名称（通过 `GET /list-accounts` 获取）。
    - 默认选中第一个账户。
    - 宽度 180px，右边距 10px。
  - **删除账户按钮**：
    - 在选择账户时显示。
    - 样式为文本型危险按钮，带删除图标。
    - 点击弹出确认对话框。
  - **交易所类型筛选下拉框**：
    - 选项：`["全部", "CEX", "DEX"]`，默认值为"全部"。
    - 宽度 120px，右边距 10px。
  - **产品类型筛选下拉框**：
    - 选项：`["全部", "现货", "永续合约"]`，默认值为"全部"。
    - 宽度 150px。
- **操作按钮**：
  - **"+ 添加 API 密钥"**：
    - 点击弹出添加密钥弹窗。
    - 主要按钮样式，带加号图标。
    - 在未选择账户时禁用。
    - 右边距 10px。
  - **"刷新"**：
    - 点击刷新表格数据。
    - 带刷新图标。
    - 刷新时显示加载状态。
- **布局**：
  - 筛选控件靠左，操作按钮靠右。
  - 整体使用 `justify-content: space-between` 实现左右分布。

#### 2.2.2 中间区域 - 账户列表表格
- **表格结构**：
  - 按 **CEX** 和 **DEX** 分组展示，每个分组使用单独的 Card 和 Table 组件。
  - **列定义**：
    1. **交易所**：显示交易所名称（如 `Binance`）。
    2. **产品类型**：显示产品类型（如 `现货`、`永续合约`）。
    3. **连接器**：显示连接器名称（如 `binance`、`binance_perpetual`）。
    4. **状态**：显示连接状态，使用带颜色的标签（绿色/黄色/红色）。
    5. **操作**：包含"查看"、"修改"、"删除"按钮。
- **分组与归类逻辑**：
  - 使用 `filteredCexConnectors` 和 `filteredDexConnectors` 计算属性分别过滤 CEX 和 DEX 连接器。
  - 每个分组使用卡片标题清晰区分（"中心化交易所 (CEX)" 和 "去中心化交易所 (DEX)"）。
- **显示控制**：
  - 通过 `exchangeConfig.ts` 中的 `visible` 属性控制交易所是否显示。
  - 默认显示：币安、OKX、Bybit、Gate.io、Bitget（CEX）和 dYdX v4、Injective（DEX）。
- **样式**：
  - 表头使用浅灰色背景、粗体字，居中对齐。
  - 表格行交替背景色，鼠标悬停高亮（淡蓝色）。
  - 所有单元格内容居中对齐。
  - 操作按钮使用 Flex 布局水平排列，居中对齐。

#### 2.2.3 空状态
- 当筛选后无数据或账户未选择时显示。
- 根据不同情况显示不同的提示文本：
  - 未选择账户："请先选择一个账户"
  - 筛选条件无匹配数据："没有符合筛选条件的数据"
  - 账户无API密钥："当前账户没有配置API密钥"
- 提供快捷操作按钮：
  - 未选择账户时显示"添加账户"
  - 已选择账户时显示"添加API密钥"

#### 2.2.4 弹窗设计
- **添加/编辑密钥弹窗**：
  - **标题**：添加时为"添加 API 密钥"，修改时为"修改 API 密钥"。
  - **控件**：
    - **账户名称**：
      - 下拉框，显示账户列表，编辑模式下禁用。
      - 支持"+ 创建新账户"选项，选择后显示输入框。
      - 表单标签使用8列宽度，输入控件使用16列宽度（右对齐布局）。
    - **交易所**：
      - 下拉框，显示配置文件中标记为可见的交易所。
      - 编辑模式下禁用。
    - **产品类型**：
      - 下拉框，根据所选交易所动态显示支持的产品类型。
      - 编辑模式下禁用。
    - **连接器**：
      - 输入框，根据交易所和产品类型自动生成，禁用编辑。
    - **密钥字段**：
      - 根据所选连接器动态生成输入框。
      - 标签使用原始字段名称。
      - 输入框使用文本类型（非密码框），便于查看输入内容。
    - **按钮**：
      - **"确认"**：提交表单，显示加载状态。
      - **"取消"**：关闭弹窗，重置表单。
  - **提交逻辑**：
    - 检查所有字段是否填写。
    - 如果是新账户，先创建账户。
    - 调用 `POST /add-connector-keys/{account_name}/{connector_name}`。
    - 成功后保存密钥到本地存储，方便查看。
    - 刷新表格数据。

- **查看详情弹窗**：
  - **标题**："查看 API 密钥"。
  - **内容**：
    - 使用 `a-descriptions` 组件展示详情。
    - 显示账户名称、交易所、产品类型、连接器名称、状态。
    - 显示完整密钥字段和值（从本地存储获取）。
    - 标签与内容均居中对齐。
  - **按钮**：
    - 无底部按钮，仅关闭按钮。

- **添加账户弹窗**：
  - **标题**："添加账户"。
  - **内容**：
    - 账户名称输入框。
    - 表单标签使用8列宽度，输入控件使用16列宽度。
    - 显示错误提示（如账户已存在）。
  - **按钮**：
    - **"确认"**：创建账户，禁用条件为空名称或有错误。
    - **"取消"**：关闭弹窗。

- **删除账户确认弹窗**：
  - **标题**："删除账户"。
  - **内容**：
    - 确认提示文本，包含账户名称。
    - 警告提示，说明操作不可恢复。
  - **按钮**：
    - **"删除"**：红色危险按钮，删除账户。
    - **"取消"**：关闭弹窗。

---

## 3. 数据流与API调用

### 3.1 页面初始化
- **API 调用**：
  - `GET /list-accounts`：获取账户列表，默认选中第一个账户。
  - `GET /list-credentials/{account_name}`：获取选中账户的连接器。
  - `GET /accounts-state`：检查密钥状态。
  - `GET /available-connectors`：获取支持的连接器列表。
- **内部处理**：
  - 解析连接器名称，确定交易所和产品类型。
  - 根据账户状态确定连接器状态（已连接/待验证/连接失败）。
  - 使用配置文件过滤和排序交易所。

### 3.2 添加/编辑 API 密钥
- **表单提交流程**：
  1. 用户选择账户（或创建新账户）、交易所、产品类型。
  2. 系统自动生成连接器名称。
  3. 调用 `GET /connector-config-map/{connector_name}` 获取所需字段。
  4. 用户填写API密钥信息。
  5. 提交表单时进行验证：
     - 所有字段必填。
     - 新账户名称有效。
  6. 调用 `POST /add-connector-keys/{account_name}/{connector_name}` 提交密钥。
  7. 成功后保存密钥到本地存储（localStorage）。
  8. 重新加载凭证列表。

### 3.3 查看 API 密钥
- **数据来源**：
  - 连接器基本信息从表格行数据获取。
  - API密钥详情从localStorage获取（用户提交成功后保存）。
- **展示方式**：
  - 使用描述列表（a-descriptions）组件展示所有字段。
  - 所有字段明文显示，方便用户查看和复制。

### 3.4 删除凭证
- **操作流程**：
  1. 点击表格中的"删除"按钮。
  2. 直接调用 `POST /delete-credential/{account_name}/{connector_name}`。
  3. 成功后刷新表格数据。
  4. 显示成功消息提示。

### 3.5 添加/删除账户
- **添加账户**：
  1. 点击"添加账户"按钮或在添加密钥时选择"创建新账户"。
  2. 输入账户名称，验证唯一性。
  3. 调用 `POST /add-account?account_name={account_name}`。
  4. 成功后刷新账户列表。
- **删除账户**：
  1. 点击"删除账户"按钮。
  2. 弹出确认对话框。
  3. 确认后调用 `POST /delete-account?account_name={account_name}`。
  4. 成功后刷新账户列表。

### 3.6 筛选功能
- **交易所类型筛选**：通过 `exchangeTypeFilter` 状态控制，过滤 CEX 或 DEX。
- **产品类型筛选**：通过 `productTypeFilter` 状态控制，过滤现货或永续合约。
- **实现**：使用计算属性 `filteredConnectors` 进行动态筛选。

### 3.7 刷新功能
- **操作**：点击"刷新"按钮。
- **执行**：重新调用 `loadAccounts`、`loadConnectors` 和 `loadCredentials` 函数。
- **意义**：获取最新账户和API状态，尤其是外部变更后。

---

## 4. 交易所配置与扩展

### 4.1 配置文件结构
- **位置**：`client/frontend/src/config/exchangeConfig.ts`
- **核心数据结构**：
  ```typescript
  interface Exchange {
    name: string;           // 交易所代码名称，如 'binance'
    label: string;          // 显示名称，如 'Binance'
    ranking: number;        // 交易所排名
    type: 'CEX' | 'DEX';    // 交易所类型
    productTypes: ProductType[]; // 支持的产品类型
    visible: boolean;       // 是否在界面上显示
  }
  
  interface ProductType {
    value: string;          // 产品类型值，如 'spot' 或 'perpetual'
    label: string;          // 显示名称，如 '现货' 或 '永续合约'
    connectorSuffix: string; // 连接器名称后缀，如 '' 或 '_perpetual'
  }
  ```

### 4.2 交易所添加/删除方式
- **添加新交易所**：
  1. 在 `exchanges` 数组中添加新对象，包含名称、标签、排名、类型等信息。
  2. 设置 `visible: true` 使其显示在界面上。
  3. 定义支持的产品类型及其连接器名称后缀。
- **删除/隐藏交易所**：
  1. 设置 `visible: false` 隐藏交易所（推荐方式，保留配置）。
  2. 或从 `exchanges` 数组中完全移除（不推荐，会丢失配置）。

### 4.3 CEX与DEX区分方式
- 通过交易所定义中的 `type` 字段区分（'CEX' 或 'DEX'）。
- 在界面上使用不同卡片分组显示。
- 提供交易所类型筛选功能。

### 4.4 现货与合约区分方式
- 通过交易所的 `productTypes` 数组定义支持的产品类型。
- 使用 `connectorSuffix` 构建完整连接器名称：
  - 现货通常后缀为空字符串（如 `binance`）。
  - 永续合约通常后缀为 `_perpetual`（如 `binance_perpetual`）。
- 提供产品类型筛选功能。

---

## 5. 美观与用户体验设计

### 5.1 视觉设计
- **主题色**：
  - 主按钮：蓝色（Ant Design 主题色）。
  - 危险操作：红色。
  - 状态标签：绿色（成功）、黄色（等待）、红色（错误）。
- **卡片分组**：
  - 标题背景色：浅蓝色 (#f5f8ff)。
  - 标题字体：粗体，居中对齐。
- **表格样式**：
  - 表头：浅灰色背景 (#fafafa)，粗体，居中对齐。
  - 单元格：内容居中对齐。
  - 行悬停：浅蓝色背景 (#f0f7ff)。

### 5.2 交互设计
- **表单布局**：
  - 标签与输入框比例为8:16，标签右对齐。
  - 弹窗标题居中对齐。
  - 错误提示文本使用红色显示。
- **操作反馈**：
  - 成功/失败消息提示。
  - 加载状态显示。
  - 操作确认对话框。
- **API密钥显示**：
  - 输入框使用文本类型（非密码框）。
  - 查看时明文显示完整密钥。
  - 本地存储保存密钥，方便查看。

### 5.3 响应式设计
- **整体布局**：
  - 主容器使用20px内边距。
  - 顶部控件使用Flex布局，自适应宽度。
  - 卡片和表格自适应容器宽度。
- **按钮与控件**：
  - 控件间距合理（10px）。
  - 按钮带图标，提升辨识度。
  - 操作按钮使用Flex布局，均匀分布。

---

## 6. 总结

### 6.1 实现特点
- **配置驱动**：使用 `exchangeConfig.ts` 控制交易所显示。
- **交易所分组**：清晰区分CEX和DEX，方便用户查找。
- **动态表单**：根据连接器自动生成字段，适应不同交易所需求。
- **本地密钥存储**：允许用户查看完整API密钥（localStorage）。
- **响应式设计**：所有元素居中对齐，布局合理，视觉美观。

### 6.2 技术实现要点
- 使用Vue.js 3 + TypeScript + Ant Design Vue组件。
- 使用计算属性实现动态筛选和分组。
- 使用API客户端拦截器统一处理认证。
- 提供详细的错误处理和状态反馈。

### 6.3 扩展性考虑
- 通过配置驱动显示，方便后续添加更多交易所。
- 考虑用户权限控制，可基于用户角色显示不同交易所。
- 支持保存API密钥和查看，提升用户体验。

这份设计满足了您的需求，既美观简洁又操作便捷，同时保留了扩展潜力，确保老板和客户看到持续优化的前景。