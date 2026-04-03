# CONTEXT

## 当前在做

- 落地 Massive/Polygon 免费档 API 小样本接入
- 把测试口径从“本地样本 / 生成样本混用”推进到“真实 API 样本优先”

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
- 文档分工调整为：
  - `README.md` 管总览与入口
  - `spec.md` 管范围与契约
  - `plan.md` 管阶段与任务依赖
  - `ARCHITECTURE.md` 管模块职责与数据流
  - `CONTEXT.md` 管当前状态与下一步
  - `docs/progress.md` 管里程碑历史

## 当前阻塞

- `fastapi`、`prefect`、`backtrader` 等可选依赖当前环境仍未装齐，无法现场验证 API / 调度 / 订单适配真实运行
- 当前环境没有 `FXMF_POLYGON_API_KEY`，无法在本地直接抓取并固化真实 fixture
- Massive/Polygon 免费档只支持最近 `2 年` 历史和 `End-of-day` recency，不适合全历史回补
- Gold 基础研究输入表还未单独沉淀，当前仍以 Silver + research 运行时计算为主
- 本地 `git push` 仍受当前环境认证链路影响

## 下一步

- 在具备 `FXMF_POLYGON_API_KEY` 后抓取并固化首份真实 fixture
- 继续推进 `B5`，补会话标注复核与 Gold 基础研究输入输出
- 继续维护 `docs/progress.md` 作为阶段性里程碑记录
