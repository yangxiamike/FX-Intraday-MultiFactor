# AGENTS.md

本文件只承担 3 个作用：

- 介绍项目背景
- 说明本项目的开发习惯
- 提供扩展文档入口

更细的开发进度、错误记录、经验总结，不直接堆在本文件里，而是拆到单独 md 文件中，通过 `@` 引用查看。

## 1. 项目背景

项目名称：

- 外汇日内单标的多因子交易系统

当前目标：

- 先完成 `USDJPY + 1m + UTC + 研究优先` 的第 1 轮闭环

当前定位：

- 这是一个先研究、后生产化的系统
- 第 1 轮重点是研究闭环，不是实盘系统
- 第 1 轮先把数据、因子研究、回测、注册表和门控骨架定清楚

## 2. 开发习惯

本项目默认遵守下面这些开发习惯：

- 先改文档，再改代码
- 先锁定边界，再扩实现
- 先做研究闭环，再补生产强化
- 数据、因子、回测、注册、门控必须统一口径
- 遇到大改动，优先更新 `spec.md`、`plan.md` 和 `ARCHITECTURE.md`
- 新会话不要直接开写代码，先读 `CONTEXT.md` 和相关文档再决定动作
- 每次开发结束后，必须同步更新受影响的文档
- 每次有效修改后，必须做对应的 git 维护

## 3. 当前核心约束

截至当前，默认约束如下：

- 标的：`USDJPY`
- 频率：`1m`
- 标准时间：`UTC`
- 数据分层：`Bronze / Silver / Gold`
- 数据接入：第 1 轮先 `文件导入`
- 注册表：开发态允许 `sqlite`，设计兼容 `PostgreSQL`
- 回测：研究层完整，订单级先骨架
- API：只做最小 FastAPI 骨架

## 4. 文档入口

新会话建议先读：

- `@README.md`
- `@CONTEXT.md`
- `@spec.md`
- `@plan.md`
- `@ARCHITECTURE.md`
- `@architecture_mindmap.md`
- `@docs/git_workflow.md`
- `@docs/progress.md`
- `@docs/errors_and_lessons.md`

## 5. 使用规则

- 如果需要理解项目总览和怎么进入：先看 `@README.md`
- 如果需要了解当前做到哪、卡在哪里、下一步干什么：先看 `@CONTEXT.md`
- 如果需要理解系统范围和契约：先看 `@spec.md`
- 如果需要理解先做什么：先看 `@plan.md`
- 如果需要快速看正式架构：先看 `@ARCHITECTURE.md`
- 如果需要快速看整体视觉结构：再看 `@architecture_mindmap.md`
- 如果需要理解 git 和开发流程：先看 `@docs/git_workflow.md`
- 如果需要回看阶段性里程碑：先看 `@docs/progress.md`
- 如果需要了解踩过哪些坑：先看 `@docs/errors_and_lessons.md`

## 6. 维护要求

后续如果出现以下情况，需要更新对应文档：

- 项目简介、运行方式、文档入口变化：更新 `README.md`
- 规格变化：更新 `spec.md`
- 开发计划变化：更新 `plan.md`
- 架构认知变化：更新 `ARCHITECTURE.md`
- 阶段性完成、阻塞变化、下一步变化：更新 `CONTEXT.md`
- 阶段性里程碑推进：更新 `docs/progress.md`
- 新的错误、坑或经验：更新 `docs/errors_and_lessons.md`
- 架构视觉补充需要同步时：更新 `architecture_mindmap.md`
- git 流程变化：更新 `docs/git_workflow.md`

## 7. 开发后强制动作

每次开发结束后，默认都要执行下面两类动作。

### 7.1 文档同步

必须根据本次修改内容，更新相关文档。

常见规则：

- 改了项目整体说明、运行方式、文档导航：更新 `README.md`
- 改了系统边界、接口语义、字段契约：更新 `spec.md`
- 改了开发顺序、阶段目标、里程碑：更新 `plan.md`
- 改了模块职责、调用关系、关键设计决策：更新 `ARCHITECTURE.md`
- 完成了阶段性任务、变更了阻塞或下一步：更新 `CONTEXT.md`
- 推进了阶段性里程碑：更新 `docs/progress.md`
- 改了整体架构可视化表达：更新 `architecture_mindmap.md`
- 遇到新错误、新坑、新经验：更新 `docs/errors_and_lessons.md`

### 7.2 Git 维护

必须根据本次修改内容，进行对应的 git 维护。

默认规则：

- 每次一组相关修改完成后，检查 `git diff`
- 只把与本次任务相关的文件纳入提交
- 提交说明要准确反映修改内容
- 文档修改和代码修改都属于需要维护 git 的内容

当前说明：

- 本地 git 仓库已初始化
- 后续每次有效修改后，本规则立即生效
