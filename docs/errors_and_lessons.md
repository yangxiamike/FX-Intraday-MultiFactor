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
