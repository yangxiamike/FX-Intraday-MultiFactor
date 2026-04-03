# 外汇日内单标的多因子交易系统

## 项目简介

本项目当前目标是完成 `USDJPY + 1m + UTC + 研究优先` 的第 1 轮闭环。

第 1 轮重点不是实盘和完整生产化，而是先把下面这条主链路跑通：

- Massive/Polygon 免费档 API 小样本接入
- 数据导入与标准化
- 因子研究与验证
- 策略级回测
- 注册表登记
- 基础门控检查

当前默认使用方式是：

- `Notebook + CLI + 最小 FastAPI`
- `Windows 主机 + Docker Desktop + 单机 Compose`

正式范围、冻结决策和验收标准以 `spec.md` 为准。

## 技术栈

- `Python 3.12`
- `uv`
- `pandas / DuckDB / PyArrow / numpy / scipy / statsmodels`
- `FastAPI`
- `Prefect 3`
- `Backtrader`（仅订单级回测适配层预留）
- `sqlite`（开发态注册表）
- `PostgreSQL`（目标兼容后端）

## 文档导航

建议阅读顺序：

1. `README.md`
2. `CONTEXT.md`
3. `spec.md`
4. `plan.md`
5. `ARCHITECTURE.md`

各文档职责：

- `README.md`：项目总览、运行方式、文档入口
- `spec.md`：范围、契约、冻结决策、验收口径
- `plan.md`：阶段顺序、任务清单、依赖关系
- `ARCHITECTURE.md`：模块职责、数据流、关键设计决策
- `CONTEXT.md`：当前在做、最近决定、阻塞、下一步
- `architecture_mindmap.md`：架构视觉补充，不作为唯一事实来源
- `docs/progress.md`：阶段性里程碑记录
- `docs/git_workflow.md`：git 与文档同步规则
- `docs/errors_and_lessons.md`：环境问题、踩坑和经验
- `docs/factor_research/*`：因子研究流程、评审模板和示例

## 本地运行

### 开发态安装后最小验证

```powershell
pip install -e .
fxmf bootstrap
set FXMF_POLYGON_API_KEY=你的key
fxmf fetch-api-sample
fxmf ingest-api-sample
fxmf demo
python -m unittest discover -s tests
```

说明：

- `fetch-api-sample` 会调用 Massive/Polygon 免费档 API 抓取固定真实小样本，并同时写入仓库 fixture 与本地缓存
- `ingest-file` 仍可用，但定位是“导入真实样本文件 / 离线回放”
- 导入完成后会同时产出 `Silver` 标准化 bars 和 `Gold` 研究基础表
- `Gold` 基础表默认包含 `session`、UTC 分钟索引以及 `Tokyo/London/NewYork/Overlap/OffSession` 标志列
- `demo` 会优先从已落盘的 `Gold research_base` 读取研究基础行，并额外输出 `forward_returns` 与 `walk_forward_splits`
- 研究侧的 correlation、rolling 统计、z-score、forward returns 主路径默认走 `numpy/pandas/scipy` 向量化实现
- 默认离线测试依赖真实 fixture；若 fixture 不存在，相关测试会明确跳过并提示先抓样本

### 安装计划依赖

```powershell
pip install uv
uv pip install --system -e .[api,backtest,db,dev,orchestration,research]
```

说明：

- 研究侧性能优化依赖 `numpy / pandas / scipy`
- 若未安装这些依赖，代码会回退到纯 Python 计算，但那只用于兜底，不是推荐运行方式

### 启动最小 FastAPI

```powershell
uvicorn services.api.app:app --reload
```

### 启动 Compose

```powershell
docker compose up --build
```

默认暴露：

- API：`http://localhost:8000`
- Prefect UI：`http://localhost:4200`
- JupyterLab：`http://localhost:8888`
- PostgreSQL：`localhost:5432`

## 常用命令

```powershell
fxmf bootstrap
fxmf fetch-api-sample
fxmf ingest-api-sample
fxmf demo
python -m unittest discover -s tests
uvicorn services.api.app:app --reload
docker compose up --build
```

## 目录结构

- `src/fx_multi_factor/data`：数据导入、标准化、分层、质量检查
- `src/fx_multi_factor/research`：标签、样本切分、研究流程
- `src/fx_multi_factor/factors`：因子定义、因子库、验证报告
- `src/fx_multi_factor/backtest`：研究回测与订单级回测适配骨架
- `src/fx_multi_factor/registry`：dataset / factor / strategy 注册表
- `src/fx_multi_factor/runtime`：Deploy Gate / Runtime Gate
- `services/api`：最小 FastAPI
- `services/worker`：Prefect 或后台任务入口
- `docs`：规划、流程、研究模板与经验文档
- `notebooks`：研究脚本与 notebook 入口
- `runtime_data`：运行时产物目录

## 文档维护约定

- 改系统范围、字段语义、接口契约：更新 `spec.md`
- 改阶段顺序、任务拆分、依赖关系：更新 `plan.md`
- 改模块边界、调用关系、架构决策：更新 `ARCHITECTURE.md`
- 每次阶段性完成后：更新 `CONTEXT.md`
- 产生新的阶段性里程碑后：更新 `docs/progress.md`
- 产生新的流程规则后：更新 `docs/git_workflow.md`
- 出现新的坑、限制或经验后：更新 `docs/errors_and_lessons.md`
