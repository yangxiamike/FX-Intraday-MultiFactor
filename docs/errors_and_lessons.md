# Errors And Lessons

版本：`v0.1`

最后更新：`2026-04-03`

## 1. 已知环境问题

### 1.1 Shell 并行命令偶发失败

现象：

- 使用并行 shell 调用时，偶发出现：
- `windows sandbox: helper_firewall_rule_create_or_add_failed`

经验：

- 单条 shell 命令更稳定
- 不要默认并行 shell 一定可靠

### 1.2 大型 apply_patch 偶发失败

现象：

- 一次性写入太多内容时，补丁可能失败

经验：

- 拆成小补丁更稳
- 文档重写时优先分段落地

### 1.3 PowerShell 直接输出中文可能乱码

现象：

- `Get-Content` 直接输出中文 md 时可能乱码

经验：

- 优先使用 UTF-8 方式读取，例如：
- `python -X utf8 -c "from pathlib import Path; print(Path('spec.md').read_text(encoding='utf-8'))"`

### 1.4 当前环境缺少核心依赖

已观察到：

- `uv` 未安装
- `pandas`
- `duckdb`
- `pyarrow`
- `fastapi`
- `prefect`
- `backtrader`

经验：

- 在依赖装齐前，不要假设系统能完整运行
- 当前阶段更适合先做文档与骨架

### 1.5 初始化前目录不是 git 仓库

已观察到：

- 初始化前，`git status` 返回当前目录不是 git repository

经验：

- 不要默认依赖 git 工作流
- 如果需要标准版本管理，要尽早初始化仓库
- 当前这个问题已处理，本地 git 已初始化

### 1.6 当前缺少直接上传 GitHub 的本机条件

已观察到：

- `gh` CLI 未安装
- 本机环境里没有可直接使用的 `GITHUB_TOKEN` / `GH_TOKEN`
- 当前也没有发现一个可直接写入的现成目标仓库

经验：

- 本地 git 初始化和本地提交可以先完成
- GitHub 上传需要额外具备远端仓库和认证路径
- 如果后续要自动上传，需补齐 `gh`、token，或先创建远端仓库

### 1.7 Git Credential Manager 当前无法提供 GitHub 凭据

已观察到：

- 本机存在 `git credential-manager`
- 但执行 `git credential fill` 获取 GitHub 凭据时失败
- 关键报错包括：
- `failed to execute prompt script`
- `fatal: could not read Username for 'https://github.com'`

经验：

- 仅安装 credential manager 不代表已经完成 GitHub 登录
- 若要自动创建远端仓库或自动 push，需要先具备真正可用的 GitHub 认证路径

### 1.8 Windows Python 可能缺少 `tzdata`

已观察到：

- 当前环境用 `zoneinfo.ZoneInfo("Europe/London")` 时直接报错
- 关键异常为 `ZoneInfoNotFoundError`

经验：

- 不要假设 Windows Python 一定自带完整 IANA 时区库
- 涉及会话标注时，优先提供 fallback 规则，或明确要求安装 `tzdata`

### 1.9 Massive/Polygon 免费档存在历史与时效限制

已观察到：

- `Currencies Basic` 只保证最近 `2 年` 历史
- recency 为 `End-of-day`
- 免费档存在调用频率限制

经验：

- 第 1 轮只能把免费档当作真实小样本验证入口，不能承诺全历史回补
- 默认测试窗口必须固定在最近 `2 年` 范围内
- 测试样本应尽量选择已完整结算的历史窗口，避免 recency 漂移

### 1.10 当前环境缺少 `FXMF_POLYGON_API_KEY`

已观察到：

- 本地没有可用的 `FXMF_POLYGON_API_KEY`
- 因此无法在当前环境直接抓取并提交首份真实 fixture

经验：

- 在线集成测试应显式跳过，不要伪造真实样本
- 离线 fixture 测试在 fixture 缺失时应明确提示，而不是回退到假数据

### 1.11 Massive/Polygon 免费档固定窗口样本可稳定作为 fixture

已观察到：

- 使用 `USDJPY 1m`
- 固定窗口 `2025-03-03 00:00:00 UTC` 到 `2025-03-03 04:00:00 UTC`
- 实际返回 `241` 根 bars
- 标准化和质量检查均通过

经验：

- 这个窗口适合作为第 1 轮默认真实 fixture
- 免费档样本应优先选择完整历史窗口，不要选接近当前时点的边界时间
- fixture 一旦固化后，应同时保留 `raw.json`、`csv` 和 `metadata.json`

### 1.12 会话标注要单独验证 DST 边界

已观察到：

- `Tokyo/London/NewYork/Overlap/OffSession` 的日常时段判断不复杂
- 真正容易出错的是 `Europe/London` 与 `America/New_York` 的 DST 切换边界

经验：

- 不要只靠真实 fixture 的单一区间验证会话标注
- 至少要补一组覆盖 London DST 切换日的单元测试
- 会话审计报告应和 Gold 研究基础表一起落盘，便于后续研究排查 session 口径

### 1.13 研究流程要复用已落盘的 Gold 基础表

已观察到：

- 如果研究流程只吃内存 bars，Gold 基础表即使已经落盘，也很容易被绕开
- 这样会让研究输入口径和落盘产物逐步偏离

经验：

- `demo` 和默认研究入口应优先从 `Gold research_base` 回读基础行
- `forward_returns` 与 `walk_forward_splits` 也应作为 Gold 产物固化，而不是只停留在运行时对象

### 1.14 研究数值计算不能长期停留在 Python for 循环

已观察到：

- correlation、rolling std、z-score、forward returns 这类计算用纯 Python 循环会很慢
- 当样本窗口和因子数量增大后，研究迭代速度会明显恶化

经验：

- 这类可向量化计算默认应使用 `numpy/pandas/scipy`
- 纯 Python 实现只能作为缺依赖回退，不能再当主实现维护

## 2. 已总结的开发经验

- 这类系统最容易出问题的地方，不是代码量，而是范围和边界不清
- 数据口径、因子口径、回测口径必须先统一，否则后面返工非常大
- 第 1 轮最重要的是研究闭环，而不是把所有生产功能一起做出来
- 文档先行比直接动手更适合当前项目阶段
- 每次开发后立即同步文档，比事后补文档更可靠
- 文档维护和 git 维护都应该被视为开发任务的一部分

## 3. 后续记录规则

后续如果出现下面任一情况，补充到本文件：

- 新的环境错误
- 新的工具限制
- 新的踩坑总结
- 可复用的工程经验
