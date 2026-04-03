# 外汇日内单标的多因子系统规格说明

版本：`v0.3-draft`

状态：`Draft`

## 1. 这份文档是干什么的

这份文档的目的只有一个：

在正式开发前，把第 1 轮要做什么、做到什么程度、哪些先不做，全部说清楚。

后面所有开发都必须以这份文档为准，不能边写边改方向。

## 1.1 文档边界

本文件只负责定义稳定内容：

- 第 1 轮范围
- 冻结决策
- 核心对象与字段语义
- 模块目标与验收口径

下面这些内容不在本文件里滚动维护：

- 当前任务、阻塞、下一步：见 `CONTEXT.md`
- 阶段顺序与任务拆解：见 `plan.md`
- 模块职责与数据流：见 `ARCHITECTURE.md`
- 架构视觉总览：见 `architecture_mindmap.md`
- 里程碑进展：见 `docs/progress.md`

## 2. 系统要解决什么问题

我们要做的是一套面向 `外汇日内交易` 的 `单标的多因子研究优先系统`。

第 1 个交易对象固定为：

- `USDJPY`

第 1 轮的目标不是实盘，不是低延迟，不是多品种组合，而是先建立一个最小但完整的研究闭环：

- 数据进入系统
- 数据被标准化和分层管理
- 可以开发和评估因子
- 可以做策略级回测
- 可以把合格结果登记进注册表
- 可以跑基础门控检查

## 3. 第 1 轮明确范围

### 3.1 必须做

- 只支持 `USDJPY`
- 只支持 `1m` K 线
- 内部统一使用 `UTC`
- 用户主要通过 `Notebook + CLI + 最小 FastAPI` 使用系统
- 数据采用 `Bronze / Silver / Gold` 三层管理
- 因子研究框架借鉴 Alphalens 思路，但重构成 `单标的时间序列因子框架`
- 回测分为：
  - `研究向量化回测`
  - `订单级回测适配层`
- 注册表包含：
  - `Dataset Registry`
  - `Factor Registry`
  - `Strategy Registry`
- 运行门控包含：
  - `Deploy Gate`
  - `Runtime Gate`

### 3.2 明确不做

- 不接真实实盘执行
- 不接 MT5 真实下单
- 不做多标的组合
- 不做 tick 级或订单簿级研究
- 不把新闻、宏观、日历在第 1 轮全部做完
- 不做完整 Web 后台
- 不做完整监控平台

## 4. 第 1 轮已经确定的 4 个关键决策

这 4 个点已经定下，不再反复摇摆。

### 4.1 注册表后端

决定：

- 第 1 轮 `开发态允许 sqlite`
- 但接口设计必须兼容 `PostgreSQL`

含义：

- 开发和本地试验时，可以先用 sqlite 单文件数据库
- 以后切换 PostgreSQL 时，不允许重写业务层

### 4.2 行情数据接入方式

决定：

- 第 1 轮必须具备 `Massive/Polygon 免费档 API 接入`
- 第 1 轮以 `真实 API 小样本验证` 为主
- `文件导入` 保留为真实样本回放路径，而不是主接入策略
- 第 1 轮研究侧可向量化数值计算默认必须走 `numpy/pandas/scipy`

含义：

- 先支持从 Massive/Polygon 免费档抓取 `USDJPY 1m` 固定历史窗口样本
- 所有测试默认基于真实 API 获取后固化的样本
- 文件导入主要用于离线复现和 fixture 回放
- 免费档限制下，不承诺全历史回补和实时能力

### 4.3 订单级回测深度

决定：

- 第 1 轮 `研究层回测做完整`
- 第 1 轮 `订单级回测只做适配骨架`

含义：

- 先把因子研究、组合回测、成本口径做扎实
- 订单生命周期和 Backtrader 深度集成先不做满

### 4.4 FastAPI 交付深度

决定：

- 第 1 轮 `FastAPI 只做最小骨架`

含义：

- 只保留健康检查和注册表查询等基础接口
- 不做完整后台系统

## 5. 设计原则

- 研究优先：先把研究闭环跑通，再逐步生产化
- 统一口径：数据、因子、回测、注册、门控必须共享同一套时间和字段语义
- 可替换：所有外部数据源都通过 provider 抽象接入
- 先简单可跑，再逐步增强：第 1 轮避免提前引入重型复杂度
- 先单标的，再扩展：避免一开始被组合问题拖慢

## 6. 技术栈

第 1 轮默认技术栈固定如下：

- 运行环境：`Windows 主机 + Docker Desktop + 单机 Compose`
- 语言：`Python 3.12`
- 包管理：`uv`
- 研究计算：`pandas + DuckDB + PyArrow/Parquet`
- 数据库：`PostgreSQL`
- 开发态注册表替身：`sqlite`
- 研究端：`JupyterLab`
- API：`FastAPI`
- 调度：`Prefect 3`
- 订单级回测底层：`Backtrader`
- 代码质量：`pytest + ruff + mypy`

约束：

- `Backtrader` 只能存在于适配层之后
- `Alphalens` 只借方法，不作为核心依赖
- 即使三方依赖还没全部装好，代码骨架也应能先跑通最小链路

## 7. 系统模块

### 7.1 data

职责：

- 定义数据集规格
- 定义 provider 抽象
- 导入原始数据
- 做标准化、时区对齐、会话标注、质量校验
- 写入 Bronze / Silver / Gold

### 7.2 research

职责：

- 计算 forward returns
- 做 walk-forward 切分
- 管理事件窗口排除
- 组织因子评估流程
- correlation、z-score、rolling mean/std、分桶统计等默认优先使用向量化实现

### 7.3 factors

职责：

- 定义 `FactorSpec`
- 管理基础因子库
- 生成 `FactorValidationReport`
- 输出 tearsheet

### 7.4 backtest

职责：

- 提供研究向量化回测
- 提供成本模型
- 提供订单级回测适配骨架

### 7.5 registry

职责：

- 注册 dataset
- 注册 factor
- 注册 strategy
- 管理状态流转和审计

### 7.6 runtime

职责：

- 实现 Deploy Gate
- 实现 Runtime Gate
- 检查数据新鲜度、点差阈值、市场状态

### 7.7 services/api

职责：

- 提供健康检查
- 提供注册表查询接口
- 为后续调度和控制面预留入口

### 7.8 services/worker

职责：

- 容纳 Prefect flow 或后台任务
- 触发导入、研究、注册、门控等流程

## 8. 数据范围与数据源策略

### 8.1 第 1 轮主数据

- `USDJPY 1m OHLC`
- `tick_volume`
- `spread_proxy`
- `provider`
- `ingest_batch_id`
- `session`

### 8.2 后续预留数据

- 经济日历
- 宏观公布值与修订值
- 利率结构与收益率曲线
- 跨资产上下文
- 新闻和事件文本

### 8.3 数据源策略

- 第 1 轮主市场数据源按 `Massive/Polygon` 的数据结构设计
- 第 1 轮必须实现 `Massive/Polygon` API 小样本接入
- 第 1 轮默认按免费档能力设计：
  - 最近 `2 年` 历史范围
  - `End-of-day` recency
  - 有频率限制
- 第 1 轮不以实时拉流为核心任务
- `文件导入` 仅作为真实样本回放路径
- `FRED/ALFRED`、`Trading Economics`、`LSEG Workspace` 先保留 provider 接口
- `MT5` 不作为第 1 轮主数据底座

## 9. 数据分层规范

### 9.1 Bronze

保存内容：

- 原始 provider payload
- 下载元数据
- ingest batch 审计信息

要求：

- 不做业务语义修改
- 可回放
- 可追溯来源

### 9.2 Silver

保存内容：

- 标准化后的 `fx_bar_1m`
- 会话标签
- UTC 对齐结果
- 数据质量报告

要求：

- 字段语义稳定
- 时间戳统一为 `UTC`
- K 线时间固定表示 `bar open time`

### 9.3 Gold

保存内容：

- 因子输入矩阵
- forward returns
- validation reports
- backtest artifacts
- signal snapshots

要求：

- 面向研究与生产复用
- 必须能追溯回 Silver 和对应 ingest batch

## 10. 时间与会话口径

固定规则：

- 内部主时间统一使用 `UTC`
- 所有输入数据进入 Silver 前都必须转成 `UTC`
- FX 一周开盘逻辑按 `24x5` 处理
- 会话至少包含：
  - `Tokyo`
  - `London`
  - `NewYork`
  - `Overlap`
- 默认保留全样本，再允许研究时按会话过滤

## 11. 关键数据对象

### 11.1 DatasetSpec

必须包含：

- `name`
- `symbol`
- `layer`
- `frequency`
- `timezone`
- `schema`
- `partition_keys`
- `version_strategy`
- `provider`

### 11.2 FXBar1m

必须包含：

- `ts`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `tick_volume`
- `spread_proxy`
- `provider`
- `ingest_batch_id`
- `session`

### 11.3 FactorSpec

必须包含：

- `name`
- `description`
- `inputs`
- `parameters`
- `lookback`
- `output_field`
- `session_filter`
- `cold_start`

### 11.4 FactorValidationReport

必须包含：

- `factor_name`
- `status`
- `sample_size`
- `horizons`
- `metrics`
- `failure_reasons`
- `generated_at`

### 11.5 StrategySpec

必须包含：

- `name`
- `version`
- `factor_weights`
- `threshold`
- `rebalance_interval`
- `allowed_sessions`
- `risk_params`

## 12. 因子研究规范

第 1 轮重点不是因子数量，而是研究流程口径固定。

必须支持：

- forward return 对齐
- IC / RankIC
- 分桶收益
- 单调性
- turnover
- stability
- decay
- cost-adjusted effect
- out-of-sample 验证
- future leak 检查

第 1 轮建议基础量价因子样例：

- 短周期 momentum
- 短周期 reversal
- rolling range position
- realized volatility
- spread pressure
- tick volume z-score

## 13. 因子准入规范

第 1 轮状态机固定为：

- `draft`
- `candidate`
- `approved`
- `retired`

规则：

- 因子开发完成先进入 `draft`
- 验证通过后进入 `candidate`
- 审核通过后进入 `approved`
- 停用或失效后进入 `retired`

## 14. 回测规范

### 14.1 VectorizedResearchBacktest

用途：

- 研究阶段快速评估
- 参数扫描
- 因子组合粗回测

### 14.2 OrderLevelBacktestAdapter

用途：

- 对接订单级语义
- 对齐持仓变化、换仓成本、成交事件
- 为未来接 Backtrader 深化实现做准备

第 1 轮限制：

- 订单级回测只要求骨架
- 不要求完整 Backtrader runtime

### 14.3 成本模型

第 1 轮至少考虑：

- spread
- slippage
- fee

## 15. 注册表规范

### 15.1 Dataset Registry

记录：

- 数据集版本
- 覆盖区间
- 质量状态
- 来源
- 存储位置

### 15.2 Factor Registry

记录：

- 因子版本
- 状态
- 指标
- report 路径
- spec 快照

### 15.3 Strategy Registry

记录：

- 策略版本
- 因子依赖
- 风险参数
- 回测引用
- 状态

## 16. 门控规范

### 16.1 Deploy Gate

至少检查：

- dataset quality
- factor status
- strategy status

### 16.2 Runtime Gate

至少检查：

- market open
- data freshness
- spread threshold
- strategy status

## 17. 最小控制面

第 1 轮 API 只需要最小能力：

- `/healthz`
- `/v1/datasets`
- `/v1/factors`
- `/v1/strategies`

第 1 轮 CLI 只需要最小能力：

- bootstrap
- fetch-api-sample
- ingest-api-sample
- demo
- registry 查看
- runtime check

## 18. 第 1 轮验收标准

只有满足下面条件，第 1 轮才算完成：

- 可以导入或生成 `USDJPY 1m` 数据
- 可以从 `Massive/Polygon` 免费档 API 拉取 `USDJPY 1m` 真实小样本
- 可以完成 Bronze / Silver / Gold 写入
- 可以对至少 3 个基础因子输出标准化 report
- 可以完成策略级回测
- 可以把 dataset / factor / strategy 写入注册表
- 可以执行 Deploy Gate 和 Runtime Gate
- 可以通过 Notebook 或 CLI 跑通一条完整示例链路

## 19. 当前结论

在后续继续编码前，第 1 轮的深度定义已经固定为：

- 注册表：`开发期 sqlite，目标兼容 PostgreSQL`
- 数据接入：`先 Massive/Polygon 免费档 API 小样本，文件导入仅作真实样本回放`
- 回测：`研究层完整，订单级先骨架`
- API：`先最小骨架，不做完整后台`

如果后续要改这 4 条，必须先改文档，再改代码。

## 20. 后续升级轮次总览

第 1 轮之后，系统按下面顺序升级。

### 第 2 轮：研究增强版

目标：

- 接入 `经济日历` 与 `宏观事件` 的真实 provider
- 引入 `因子维护` 与 `因子监测` 机制
- 建立 `因子失效检测`、`稳定性监控`、`再验证` 流程
- 扩展 `跨资产上下文特征`

新增重点：

- `FRED/ALFRED`
- `Trading Economics`
- 因子监测作业
- 因子再验证报告
- 因子下线规则

### 第 3 轮：生产骨架版

目标：

- 把研究端与生产端连接起来
- 补齐 `Strategy Registry`
- 补齐 `Deploy Gate` 和 `Runtime Gate` 的正式检查项
- 引入 `Scheduler`、`Monitoring`、`Paper Trading`

新增重点：

- 更完整的调度体系
- paper trading
- 运行状态面板
- 日志、指标、告警

### 第 4 轮：执行与风控增强版

目标：

- 接入真实执行通道
- 加入账户容量与策略偏离感知
- 加入更严格的运行时风控

新增重点：

- MT5 或其它执行适配器
- execution adapter
- account capacity
- strategy drift detection
- execution quality analysis

### 第 5 轮：高级数据与完整生产版

目标：

- 接入新闻、事件文本、复杂参考数据
- 引入 `LSEG Workspace` 等高级数据源
- 把系统从“研究优先骨架”升级为“完整生产化框架”

新增重点：

- 新闻和事件管线
- 利率曲线与复杂参考数据
- 更完整的监控与故障恢复
- 更强的生产运维能力

### 升级顺序约束

后续几轮必须遵守：

- 先完成第 1 轮研究闭环
- 再接宏观/日历与因子维护
- 再做生产骨架
- 再做真实执行
- 最后做高级数据和完整生产化
