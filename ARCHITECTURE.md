# ARCHITECTURE

## 模块划分

- `data`：定义数据集契约、provider 抽象、Massive/Polygon API 小样本接入、真实样本回放导入、标准化、UTC 对齐、会话标注、质量检查、Bronze / Silver / Gold 写入
- `research`：生成 forward returns、walk-forward 切分、事件窗口处理、组织单因子与多因子研究流程
- `factors`：定义 `FactorSpec`、维护基础因子库、输出 `FactorValidationReport` 与 tearsheet
- `backtest`：提供研究向量化回测、成本模型、订单级回测适配骨架
- `registry`：管理 dataset / factor / strategy 注册、状态流转与审计信息
- `runtime`：实现 Deploy Gate / Runtime Gate，检查 market open、freshness、spread、状态等门控项
- `services/api`：提供 `/healthz` 和注册表查询等最小接口
- `services/worker`：承载 Prefect flow 或后台任务，串联导入、研究、注册、门控流程
- `notebooks`：研究入口，优先调用库层而不是沉淀临时逻辑

## 数据流/调用关系

1. Massive/Polygon 免费档 API 先拉取 `USDJPY 1m` 固定真实样本窗口
2. 原始 API 响应写入 `Bronze`，并同步固化为测试 fixture 与本地缓存
3. 标准化、UTC 对齐、会话标注和质量检查后产出 `Silver`
4. `data` 基于 `Silver` bars 继续沉淀 `Gold research_base`，固定输出 UTC 分钟、session 标签和会话标志列
5. 研究输入、forward returns、因子输入矩阵和回测产物写入 `Gold`
6. `research` 与 `factors` 基于 `Gold` 产出验证报告和 tearsheet
7. `backtest` 基于因子结果和策略定义输出研究回测结果与订单级事件骨架
8. `registry` 记录 dataset / factor / strategy 的版本、状态和引用关系
9. `runtime` 组合注册表状态和运行时上下文，返回 Deploy Gate / Runtime Gate 结果
10. `Notebook`、`CLI`、`FastAPI` 作为统一入口消费上述能力

## 关键设计决策

- 第 1 轮范围固定为 `USDJPY + 1m + UTC + 研究优先`
- 数据管理统一采用 `Bronze / Silver / Gold`
- 外部数据源必须通过 provider 抽象接入，第 1 轮优先 `Massive/Polygon` 免费档 API 小样本
- 文件导入保留为真实样本回放路径，不再作为主接入策略
- `Gold research_base` 作为第 1 轮固定研究输入底表，由数据层直接从 `Silver` bars 沉淀
- 注册表开发态允许 `sqlite`，但接口设计必须兼容 `PostgreSQL`
- 回测分两层：研究向量化回测做完整，订单级回测先保留适配骨架
- `Backtrader` 只能隐藏在适配层之后，不能污染业务对象模型
- API 只交付最小 FastAPI 骨架，不提前扩成完整后台

## 已知约束

- 第 1 轮不接真实实盘执行、不做 MT5 真连接
- 第 1 轮不做多标的组合、不做 tick 级或订单簿级研究
- 第 1 轮不把新闻、宏观、日历全部接完
- Massive/Polygon 免费档只承诺最近 `2 年` 历史和 `End-of-day` recency
- `architecture_mindmap.md` 只做视觉补充，正式架构语义以本文件和 `spec.md` 为准
- 当前代码骨架需要持续对照 `spec.md` 与 `plan.md` 做偏航检查
