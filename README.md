# 外汇日内单标的多因子交易系统

## 项目简介

本项目当前目标是完成 `USDJPY + 1m + UTC + 研究优先` 的第 1 轮闭环。

第 1 轮重点不是实盘和完整生产化，而是先把下面这条主链路跑通：

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
fxmf ingest-file .\data\usdjpy_1m.csv
fxmf demo
python -m unittest discover -s tests
```

### 安装计划依赖

```powershell
pip install uv
uv pip install --system -e .[api,backtest,db,dev,orchestration,research]
```

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
fxmf ingest-file .\data\usdjpy_1m.csv
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
