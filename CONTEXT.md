# CONTEXT

## 当前在做

- 对照 `spec.md`、`plan.md`、`ARCHITECTURE.md` 评估现有代码骨架是否偏航
- 准备把第 1 轮任务从“文档已冻结”推进到“按任务组逐项落地”

## 上次做到哪里

- 已完成规划文档职责边界整理
- 已补齐 `README.md`、`ARCHITECTURE.md`、`CONTEXT.md`
- 已把 `spec.md`、`plan.md`、`architecture_mindmap.md`、`docs/progress.md` 调整为“主文档 + 引用补充”的关系
- 仓库中已存在一批 `src/`、`services/`、`sql/` 早期骨架

## 最近关键决定

- 第 1 轮固定为 `USDJPY + 1m + UTC + 研究优先`
- 注册表：开发态允许 `sqlite`，目标兼容 `PostgreSQL`
- 数据接入：第 1 轮先做 `文件导入`
- 回测：研究层完整，订单级先骨架
- API：只做最小 `FastAPI`
- 文档分工调整为：
  - `README.md` 管总览与入口
  - `spec.md` 管范围与契约
  - `plan.md` 管阶段与任务依赖
  - `ARCHITECTURE.md` 管模块职责与数据流
  - `CONTEXT.md` 管当前状态与下一步
  - `docs/progress.md` 管里程碑历史

## 当前阻塞

- 现有代码骨架尚未逐模块对照 `spec.md` / `plan.md` 做偏航检查
- 核心依赖尚未装齐，当前更适合先推进文档与骨架一致性
- 本地 `git push` 仍受当前环境认证链路影响

## 下一步

- 对照 `spec.md`、`plan.md`、`ARCHITECTURE.md` 审视现有代码骨架是否偏航
- 把第 1 轮任务从“文档已定义”推进到“按任务组逐项落地”
- 继续维护 `docs/progress.md` 作为阶段性里程碑记录
