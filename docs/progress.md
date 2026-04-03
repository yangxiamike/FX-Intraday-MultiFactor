# Development Progress

版本：`v0.4`

最后更新：`2026-04-03`

说明：

- 本文件记录阶段性里程碑，不替代 `CONTEXT.md` 的滚动状态
- 当前任务、阻塞、下一步以 `CONTEXT.md` 为准

## 1. 当前阶段

当前处于：

- 真实 fixture 驱动的研究产物固化阶段

当前原则：

- 先修正文档与代码骨架之间的显式偏航
- 先补最小可执行入口，再进入数据链路正式落地

## 2. 已完成事项

截至当前，已经完成：

- 明确系统目标是 `USDJPY + 1m + UTC + 研究优先`
- 完成第 1 轮规格文档 `spec.md`
- 完成开发计划文档 `plan.md`
- 完成项目总览文档 `README.md`
- 完成正式架构文档 `ARCHITECTURE.md`
- 完成滚动状态文档 `CONTEXT.md`
- 完成工程框架思维导图 `architecture_mindmap.md`
- 建立项目级 `AGENTS.md`
- 建立 git 工作流文档 `docs/git_workflow.md`
- 明确规划文档职责边界与引用关系
- 初始化本地 git 仓库
- 完成本地第 1 个提交
- 仓库中已经存在一批早期代码骨架文件
- 补齐 `src/fx_multi_factor/cli.py`，实现 `bootstrap / demo / registry / runtime-check`
- 补齐 `fxmf ingest-file`，支持本地 `CSV` 导入到 Bronze / Silver 并登记 dataset registry
- 补齐 `services/api/app.py`，实现 `/healthz`、`/v1/datasets`、`/v1/factors`、`/v1/strategies`
- 新增最小 `unittest`，覆盖 bootstrap、demo、runtime-check 主路径
- 新增文件导入测试，覆盖本地 CSV 导入主路径
- 固化 `NormalizationReport` 与 Silver 元数据结构，明确 UTC / bar-open / session 语义
- 增强 `DataQualityReport`，补齐重复、缺口、非法价格、非整分钟时间戳等摘要字段
- 新增质量检查测试，覆盖非整分钟时间戳告警
- 补上 Massive/Polygon 免费档 provider 实现骨架
- 新增 `fetch-api-sample / ingest-api-sample` 命令
- 将 `demo` 和测试主路径切换到真实 fixture 优先
- 已固化首份真实 `USDJPY 1m` fixture：`2025-03-03 00:00:00 UTC` 到 `2025-03-03 04:00:00 UTC`，共 `241` 根 bars
- 已完成离线真实 fixture 测试与在线集成测试验证
- 已补上 `Gold research_base` 基础表与会话审计报告
- 已补上 London DST 边界与 Tokyo/London/NewYork/Overlap/OffSession 会话分类测试
- 已补上 `forward_returns` 与 `walk_forward_splits` 固化产物
- `demo` 已优先从已落盘的 `Gold research_base` 读取研究基础输入
- 已将 rolling 因子、correlation 与 `forward_returns` 改为优先向量化实现
- `demo` 已补上聚合 `factor_summary` 与 markdown `factor_tearsheet` 输出
- 研究引擎已补上 `session / vol_regime / trend_regime / event_flag` 分块评估
- 修复 `registry` sqlite 连接未显式关闭问题
- 修复缺少 `tzdata` 时 `session` 标注直接失败的问题
- 新建仓库根目录 `.venv` 作为统一正式测试环境，并安装完整依赖组
- 已补上 `FastAPI`、注册表存储、向量化回测、runtime gate 的自动化测试
- 已在统一 `.venv` 环境完成全量 `unittest` 回归：`20 passed, 2 skipped`
- 已确认跳过项为在线集成测试，需 `FXMF_POLYGON_API_KEY` 且 `FXMF_RUN_LIVE_TESTS=1`

## 3. 当前已存在的代码骨架

仓库中已经存在但尚未完全冻结方向的内容包括：

- `pyproject.toml`
- `docker-compose.yml`
- `src/fx_multi_factor/...`
- `services/...`
- `sql/...`

说明：

- 这些文件代表早期骨架已经开始形成
- 当前已完成第一轮偏航修正，至少入口层承诺与代码实现已对齐
- 后续仍需继续按任务组审视并补齐数据链路细节

## 4. 第 1 轮当前确认状态

已经确认：

- 注册表：开发态允许 `sqlite`
- 目标数据库：`PostgreSQL`
- 数据接入：第 1 轮主路径切换到 `Massive/Polygon` 免费档 API 小样本
- 回测：`研究层完整，订单级先骨架`
- API：只做最小 `FastAPI`

## 5. 下一阶段重点

下一阶段重点是：

1. 补齐 provider 失败路径、数据质量异常样本、向量化主/回退双路径测试
2. 收敛当前 `numpy` runtime warning（相关性/方差退化窗口）
3. 在现有分块评估基础上继续补更细的外部事件标签与独立配置层
4. 持续维护 `CONTEXT.md` 与 `docs/progress.md` 的分层记录

## 6. Git 状态

当前已完成：

- 本地 git 仓库已初始化
- 主分支为 `main`
- 已完成首个本地提交
- GitHub 远端仓库已建立并完成首轮代码上传
- 远端仓库：`yangxiamike/FX-Intraday-MultiFactor`

当前未完成：

- 本地 `git push` 仍受当前环境认证链路影响

## 7. 后续升级路线

后续几轮已经有方向，但还未进入实现：

- 第 2 轮：研究增强与因子维护
- 第 3 轮：生产骨架升级
- 第 4 轮：执行层与风控升级
- 第 5 轮：高级数据与完整生产化

## 8. 更新规则

每次下面任一事项发生，都要更新本文件：

- 新完成一个里程碑
- 进入新阶段
- 增加关键文档
- 开始或停止某条实现路线
- 完成一轮实际开发并产生有效修改
- 如果只是当前任务、阻塞或下一步变化，优先更新 `CONTEXT.md`
