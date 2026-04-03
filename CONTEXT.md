# CONTEXT

## 当前在做

- 在统一 `.venv` 环境下持续做全量绿灯回归
- 继续补 provider 失败路径、数据质量异常样本、向量化主/回退双路径测试

## 上次做到哪里

- 已完成规划文档职责边界整理
- 已补齐 `README.md`、`ARCHITECTURE.md`、`CONTEXT.md`
- 已把 `spec.md`、`plan.md`、`architecture_mindmap.md`、`docs/progress.md` 调整为“主文档 + 引用补充”的关系
- 已识别出早期骨架的入口层偏航：`pyproject.toml` 已声明 CLI，但代码中缺少 `cli.py`
- 已补上 `fxmf` CLI、最小 `FastAPI` 入口，以及基于真实 fixture 的本地 demo 流程
- 已在 CLI 中补上 `ingest-file`，把 `LocalCsvMarketDataProvider` 接成正式文件导入入口
- 已补上标准化摘要 `NormalizationReport`，并把 Silver 元数据固定为可复用结构
- 已补上质量报告摘要字段，覆盖 `1m` 频率、重复、缺口、非法价格、非整分钟时间戳等检查
- 已补上 Massive/Polygon 免费档 provider 骨架和 `fetch-api-sample / ingest-api-sample` CLI 入口
- `demo` 已切换为优先消费真实 fixture；若 fixture 缺失，会明确提示先抓取真实样本
- 已抓取并固化首份真实 fixture：`2025-03-03 00:00:00 UTC` 到 `2025-03-03 04:00:00 UTC`，共 `241` 根 `USDJPY 1m` bars
- 已完成离线真实 fixture 测试与在线集成测试验证
- 已完成 `B5` 主体：会话审计报告、Gold `research_base` 基础表、DST 边界会话测试
- 已完成 `C2` 基础落地：`forward_returns` 与 `walk_forward_splits` 产物已落盘
- `demo` 已切到优先读取已落盘的 `Gold research_base`
- 已将 rolling 因子、correlation 与 `forward_returns` 改为“优先向量化，缺依赖回退”的实现
- 已补上聚合 `factor_summary` 与 markdown `factor_tearsheet` 产物，并接入 `demo`
- 已补上 `session / vol_regime / trend_regime / event_flag` 分块评估，并写入 factor report / summary / tearsheet
- 已创建项目专用 `.venv`，并安装 `-e .[api,backtest,db,dev,orchestration,research]`
- 已确认现有测试需在 `.venv` 下执行，旧 `mt5` 环境不再作为正式测试环境
- 已补齐 `FastAPI`、注册表、向量化回测、runtime gate 的规则级测试
- 已在统一 `.venv` 环境完成全量 `unittest` 回归，当前为 `20 passed, 2 skipped`
- 已确认 `2 skipped` 为在线集成测试，条件是 `FXMF_POLYGON_API_KEY` 且 `FXMF_RUN_LIVE_TESTS=1`

## 最近关键决定

- 第 1 轮固定为 `USDJPY + 1m + UTC + 研究优先`
- 注册表：开发态允许 `sqlite`，目标兼容 `PostgreSQL`
- 数据接入：第 1 轮主路径改为 `Massive/Polygon 免费档 API 小样本`
- 回测：研究层完整，订单级先骨架
- API：只做最小 `FastAPI`
- `文件导入` 保留为真实样本回放路径，默认支持 `CSV`
- 所有测试默认只认真实 API 获取后固化的样本；不再以生成假行情作为正式测试输入
- 会话标注在缺少 `tzdata` 的 Windows Python 环境下增加内置 fallback，避免基础流程因时区库缺失而中断
- Silver 层元数据固定包含：数据集基础信息、时间语义、标准化摘要、质量报告
- Gold `research_base` 元数据固定包含：研究输入字段列表、会话审计报告、来源层说明
- 第 1 轮 `walk_forward_splits` 固定使用 `120/60/60` bars 结构，先保证切分口径稳定
- 研究侧数值计算主路径改为 `numpy/pandas` 向量化，纯 Python 实现只保留为缺依赖回退
- 正式测试环境统一固定为仓库根目录 `.venv`
- 每进入下一步开发前，必须先完成当前已存在测试的全量绿灯回归
- 文档分工调整为：
  - `README.md` 管总览与入口
  - `spec.md` 管范围与契约
  - `plan.md` 管阶段与任务依赖
  - `ARCHITECTURE.md` 管模块职责与数据流
  - `CONTEXT.md` 管当前状态与下一步
  - `docs/progress.md` 管里程碑历史

## 当前阻塞

- Massive/Polygon 免费档只支持最近 `2 年` 历史和 `End-of-day` recency，不适合全历史回补
- `Gold research_base` 已被研究流程复用，但更细的事件窗口与样本过滤还未沉淀成独立配置层
- `event_flag` 当前只支持来自研究参数 `event_windows` 的显式窗口，尚未接外部事件源
- 本地 `git push` 仍受当前环境认证链路影响
- 现有测试虽然已绿，但向量化相关计算仍会打印 `numpy` runtime warning，后续需要判断是预期容错还是需要收敛成静默处理

## 下一步

- 继续补 provider 失败路径、数据质量异常样本、向量化主/回退双路径测试
- 收敛当前 `numpy` runtime warning（相关性/方差退化窗口）
- 在现有分块评估基础上继续补更细的外部事件标签与独立配置层
- 视需要刷新或扩充真实 fixture 窗口，但保持免费档约束内的小样本策略
- 继续维护 `docs/progress.md` 作为阶段性里程碑记录
