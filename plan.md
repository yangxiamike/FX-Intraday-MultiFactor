# 外汇日内单标的多因子系统开发计划

版本：`v0.4-draft`

状态：`Draft`

## 1. 这份计划是干什么的

这份计划负责回答：

- 开发先后顺序是什么
- 每一阶段做到什么算完成
- 哪些事情必须后置

这份计划和 `spec.md` 配套使用。

## 1.1 文档分工

本文件只负责稳定的规划内容：

- 开发阶段顺序
- 任务组拆分
- 依赖关系
- 退出条件

下面这些内容不在本文件里滚动维护：

- 当前做到哪里、卡在哪里、下一步做什么：见 `CONTEXT.md`
- 模块职责和数据流：见 `ARCHITECTURE.md`
- 范围、字段语义和验收口径：见 `spec.md`
- 阶段性里程碑记录：见 `docs/progress.md`

## 2. 总体开发策略

第 1 轮开发必须遵守下面 6 条：

- 先定规格，再写实现
- 先跑通主链路，再补增强能力
- 先研究闭环，再生产强化
- 每一阶段必须有明确退出条件
- 每次开发后必须同步更新受影响文档
- 每次有效修改后必须进行对应的 git 维护

## 3. 第 1 轮已经锁定的策略

这些点已经确认：

- 注册表：开发态允许 sqlite，接口兼容 PostgreSQL
- 数据接入：先做 Massive/Polygon 免费档 API 小样本接入，文件导入用于真实样本回放
- 回测：研究层先做完整，订单级只做适配骨架
- API：先做最小骨架，不做完整后台

这意味着：

- 第 1 轮重点不是“把所有系统都做出来”
- 第 1 轮重点是“把研究闭环真正跑通”

## 4. 阶段划分

### 阶段 0：规格冻结

目标：

- 把 `spec.md` 与 `plan.md` 固化下来
- 把第 1 轮的边界和深度说清楚

交付物：

- `spec.md`
- `plan.md`

退出条件：

- 用户确认第 1 轮范围
- 用户确认 4 个关键决策已经固定

### 阶段 1：工程骨架

目标：

- 建立项目目录结构
- 建立依赖管理、测试、类型检查和 Compose 骨架

交付物：

- 项目目录结构
- `pyproject.toml`
- `docker-compose.yml`
- `README.md`
- 最小 CLI / API 入口

退出条件：

- 项目结构稳定
- 代码可以安装或以开发态运行
- 不再对目录结构频繁返工

### 阶段 2：数据链路

目标：

- 打通 `USDJPY 1m` 数据从输入到 Bronze / Silver / Gold 的流程
- 完成标准化、UTC 对齐、会话标注、质量检查

交付物：

- provider 抽象
- Massive/Polygon API provider
- 真实样本 fixture
- 文件导入器（真实样本回放）
- ingest pipeline
- data lake layout
- quality report

退出条件：

- 一组真实 API 小样本可以完整入湖
- 可以输出质量报告
- 可以追溯到 ingest batch

### 阶段 3：因子研究链路

目标：

- 建立单标的时间序列因子研究框架
- 完成基础量价因子样例
- 输出标准化 validation report 和 tearsheet

交付物：

- FactorSpec
- forward returns
- 因子评估指标
- tearsheet

退出条件：

- 至少 3 个基础因子可以稳定跑出报告
- 报告结构不再频繁变动

### 阶段 4：回测链路

目标：

- 完成研究向量化回测
- 完成订单级回测适配骨架
- 固定成本模型

交付物：

- VectorizedResearchBacktest
- OrderLevelBacktestAdapter
- CostModel
- StrategySpec

退出条件：

- 因子组合可以输出回测结果
- 可以生成信号快照
- 可以生成订单事件骨架

### 阶段 5：注册表与门控

目标：

- 完成 dataset / factor / strategy 注册表
- 完成 Deploy Gate / Runtime Gate
- 提供最小查询接口

交付物：

- registry store
- lifecycle 状态管理
- gate checks
- 最小 API 查询能力

退出条件：

- 数据、因子、策略可注册
- gate 可以返回结构化结果

### 阶段 6：端到端验收

目标：

- 跑通一条完整示例链路

交付物：

- demo flow
- demo outputs
- 验收记录

退出条件：

- `导入 -> 研究 -> 验证 -> 回测 -> 注册 -> 门控` 全链路成功

## 5. 建议执行顺序

严格按下面顺序推进：

1. 固化 `spec.md`
2. 固化 `plan.md`
3. 只搭工程骨架
4. 先做数据链路
5. 再做因子研究
6. 再做回测
7. 最后补注册表、门控和最小 API

原因很简单：

- 数据口径不稳定，后面全部返工
- 因子报告结构不稳定，注册表就定不住
- API 和服务化做得太早，前期收益很低

## 6. 哪些事情必须后置

下面这些内容不应该抢在第 1 轮前面：

- 实盘执行
- MT5 真连接
- 多标的组合
- 新闻文本管线
- 宏观和日历的完整接入
- 完整 Web 后台
- 完整监控平台
- 完整 Backtrader 运行时
- 自动化 API 拉数体系

## 7. 风险与控制

### 风险 1：一开始就把生产复杂度带进来

控制：

- 第 1 轮只做研究优先闭环
- 所有生产相关最多做到骨架

### 风险 2：数据源绑定过深

控制：

- 所有数据源通过 provider 抽象
- 第 1 轮优先文件导入

### 风险 3：回测框架绑定过深

控制：

- Backtrader 只能隐藏在适配层之后
- 业务逻辑不得直接依赖 Backtrader 对象模型

### 风险 4：边开发边改规格

控制：

- 先改文档，再改代码
- 每一轮实现都必须能在 `spec.md` 中找到依据

## 8. 编码前检查清单

继续大规模编码前，应确认：

- `spec.md` 已通过
- `plan.md` 已通过
- 第 1 轮边界已通过
- 数据分层口径已通过
- 因子研究指标已通过
- 回测深度已通过
- 注册表与门控范围已通过

## 9. 每次开发完成后的收尾要求

每次完成一轮开发后，都必须做收尾，不允许只改代码不维护文档。

### 9.1 文档收尾

至少检查下面几类文档是否要更新：

- `spec.md`
- `plan.md`
- `architecture_mindmap.md`
- `docs/progress.md`
- `docs/errors_and_lessons.md`

原则：

- 改到哪里，文档就维护到哪里
- 文档更新属于开发的一部分，不是可选项

### 9.2 Git 收尾

每次完成一组相关修改后，都要进行 git 维护。

最低要求：

- 查看本次 diff
- 确认修改范围
- 只纳入本次任务相关文件
- 使用能反映修改内容的提交说明

说明：

- 本地 git 仓库已初始化
- 从现在开始，每次有效修改后都应执行本要求

## 10. 执行状态记录位置

本文件不再维护“当前建议的下一步”这类滚动状态。

统一规则：

- 当前任务、阻塞、下一步：更新 `CONTEXT.md`
- 阶段性完成记录：更新 `docs/progress.md`
- 只有当阶段顺序、任务拆分或依赖关系变化时，才更新本文件

## 11. 后续升级路线

第 1 轮完成后，后续按下面几轮升级。

### 第 2 轮：研究增强与因子维护

目标：

- 接入日历和宏观 provider
- 因子研究从“一次性评估”升级为“持续维护”
- 建立因子监测、复核、退役流程

关键交付物：

- 宏观 / 日历数据适配器
- 因子监测任务
- 再验证报告
- 因子生命周期管理增强

进入条件：

- 第 1 轮研究闭环已经稳定

### 第 3 轮：生产骨架升级

目标：

- 从研究闭环升级到准生产闭环
- 补齐调度、监控、paper trading、正式门控

关键交付物：

- paper trading
- scheduler 强化
- monitoring
- 更完整的 Deploy Gate / Runtime Gate

进入条件：

- 第 2 轮的数据与因子维护链路稳定

### 第 4 轮：执行层与风控升级

目标：

- 接入真实执行适配器
- 引入容量、偏离和执行质量分析

关键交付物：

- execution adapter
- account capacity 模块
- strategy drift detection
- execution quality report

进入条件：

- 第 3 轮准生产链路稳定

### 第 5 轮：高级数据与完整生产化

目标：

- 接入新闻、复杂参考数据、LSEG Workspace
- 完成更完整的生产化强化

关键交付物：

- 新闻与事件文本管线
- LSEG Workspace 适配器
- 高级参考数据处理
- 更完整的生产运维能力

进入条件：

- 第 4 轮执行与风控能力稳定

## 12. 文档配套与引用规则

项目规划文档统一按下面方式协作：

- `README.md`：项目总览、运行方式、文档入口
- `spec.md`：稳定范围、冻结决策、契约与验收口径
- `plan.md`：阶段顺序、任务清单、依赖关系
- `ARCHITECTURE.md`：模块职责、调用关系、关键设计决策
- `CONTEXT.md`：当前状态、最近决定、阻塞、下一步
- `docs/progress.md`：里程碑历史
- `architecture_mindmap.md`：视觉补充
- `AGENTS.md`：协作规则与文档入口约束

要求：

- 同一事实尽量只保留一个主文档，其它文档通过引用说明
- 当前优先级和临时状态不要散落在 `README.md`、`spec.md`、`plan.md` 里重复维护
- 新会话默认先读 `CONTEXT.md`，再按任务需要进入 `spec.md`、`plan.md`、`ARCHITECTURE.md`

## 13. 第 1 轮可执行任务清单

下面这部分是第 1 轮真正的实施清单。后续开发默认按这里推进。

### 13.1 任务组 A：项目基础设施

任务 A1：初始化项目工程结构

- 输入：已确认的 `spec.md` 和 `plan.md`
- 输出：稳定的目录结构、基础配置文件、基础说明文档
- 验收条件：目录结构不再反复调整；新模块可以按规划放置

任务 A2：建立 Python 工程基线

- 输入：目标技术栈
- 输出：`pyproject.toml`、依赖分组、lint/test/type-check 基线
- 验收条件：本地或开发态可以完成最小安装与静态检查入口

任务 A3：建立运行与开发容器骨架

- 输入：服务清单
- 输出：`docker-compose.yml`、基础 Dockerfile、服务占位入口
- 验收条件：服务结构与架构设计一致；后续模块可以直接挂接

### 13.2 任务组 B：数据链路

任务 B1：定义数据对象与数据集契约

- 输入：`DatasetSpec`、`FXBar1m`、数据分层规范
- 输出：统一数据对象定义
- 验收条件：研究、回测、注册表使用同一套字段语义

任务 B2：实现文件导入入口

- 输入：CSV/Parquet/批量历史文件
- 输出：真实样本回放导入器和 ingest batch 记录
- 验收条件：一份基于真实 API 获取的 `USDJPY 1m` 样本文件可被系统读入

任务 B2A：实现 Massive/Polygon 免费档 API 小样本接入

- 输入：`USDJPY 1m`、固定历史窗口、`FXMF_POLYGON_API_KEY`
- 输出：真实 API 样本下载命令、fixture 刷新命令
- 验收条件：可从免费档拉取最近 2 年内固定历史窗口的小样本

任务 B3：实现标准化与 Silver 写入

- 输入：原始文件数据
- 输出：UTC 对齐后的标准化 `fx_bar_1m`
- 验收条件：字段完整、时间语义清晰、可追溯来源

任务 B4：实现数据质量检查

- 输入：标准化 bars
- 输出：质量报告
- 验收条件：至少能识别重复、缺口、非法价格、时区问题

任务 B5：实现会话标注与 Gold 基础输出

- 输入：Silver 数据
- 输出：会话标签、Gold 研究输入基础表
- 验收条件：Tokyo/London/NewYork/Overlap 口径可复用

### 13.3 任务组 C：因子研究

任务 C1：定义 `FactorSpec`

- 输入：因子研究规范
- 输出：统一因子描述对象
- 验收条件：每个因子都能声明依赖、参数、lookback、输出名

任务 C2：实现 forward returns 与样本切分

- 输入：Gold 基础输入
- 输出：forward returns、walk-forward 切分
- 验收条件：无未来函数；切分逻辑稳定

任务 C3：实现基础量价因子库

- 输入：价格、tick volume、spread_proxy
- 输出：至少 3-6 个基础因子
- 验收条件：因子可稳定输出，不依赖临时 notebook 逻辑

任务 C4：实现因子评估与 tearsheet

- 输入：因子值与 forward returns
- 输出：IC / RankIC / 分桶 / decay / turnover / OOS 等报告
- 验收条件：至少 3 个因子可生成结构化报告

### 13.4 任务组 D：回测

任务 D1：定义 `StrategySpec` 和 `CostModel`

- 输入：回测规范
- 输出：统一策略与成本对象
- 验收条件：研究层和订单层共用同一成本语义

任务 D2：实现研究向量化回测

- 输入：因子结果与策略定义
- 输出：收益曲线、回撤、换手、信号快照
- 验收条件：可对多因子组合进行稳定粗回测

任务 D3：实现订单级回测适配骨架

- 输入：策略目标仓位
- 输出：订单事件、持仓变动、成交占位逻辑
- 验收条件：保留未来接入 Backtrader 的接口，但不深绑

### 13.5 任务组 E：注册表与门控

任务 E1：实现 Dataset Registry

- 输入：数据集元信息与质量结果
- 输出：dataset 注册记录
- 验收条件：可追溯版本、覆盖区间、来源、状态

任务 E2：实现 Factor Registry

- 输入：因子 spec 与评估结果
- 输出：factor 注册记录与状态流转
- 验收条件：支持 `draft -> candidate -> approved -> retired`

任务 E3：实现 Strategy Registry

- 输入：策略定义与回测引用
- 输出：strategy 注册记录
- 验收条件：可查询策略版本和依赖关系

任务 E4：实现 Deploy Gate / Runtime Gate

- 输入：dataset / factor / strategy / 运行时上下文
- 输出：结构化 gate result
- 验收条件：至少覆盖 quality、status、freshness、spread、market open

### 13.6 任务组 F：最小入口与验收

任务 F1：实现最小 CLI

- 输入：核心模块
- 输出：bootstrap、fetch-api-sample、ingest-api-sample、demo、registry、runtime check 命令
- 验收条件：无 UI 情况下也能走完整示例链路

任务 F2：实现最小 FastAPI

- 输入：注册表与健康状态
- 输出：`/healthz`、`/v1/datasets`、`/v1/factors`、`/v1/strategies`
- 验收条件：接口结构稳定，后续可扩展

任务 F3：完成第 1 轮端到端 demo

- 输入：前面所有任务产物
- 输出：`导入 -> 研究 -> 验证 -> 回测 -> 注册 -> 门控` 示范链路
- 验收条件：可重复执行并产生可检查结果

## 14. 第 1 轮任务依赖关系

默认依赖如下：

1. A 先于 B
2. B 先于 C
3. C 先于 D
4. B、C、D 先于 E
5. B、C、D、E 先于 F

说明：

- 如果底层数据口径没定，不允许先补因子和回测
- 如果因子输出结构没定，不允许先补注册表

## 15. Git 与文档流程要求

第 1 轮开发时，必须同时遵守：

- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `CONTEXT.md`
- `docs/progress.md`
- `docs/errors_and_lessons.md`
- `docs/git_workflow.md`

要求：

- 每完成一组任务，都要更新相关文档
- 每完成一组任务，都要做 git 维护
