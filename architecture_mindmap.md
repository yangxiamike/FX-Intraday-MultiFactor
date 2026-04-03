# 外汇日内单标的多因子系统工程框架思维导图

这份文档用于从架构视角快速看到系统全貌。

说明：

- 本文件是视觉补充，不是唯一的架构事实来源
- 正式模块职责、调用关系和关键设计决策以 `ARCHITECTURE.md` 为准
- 范围、字段语义和验收口径以 `spec.md` 为准

```mermaid
mindmap
  root((FX 日内单标的多因子系统))
    第1轮
      数据层
        Bronze
        Silver
        Gold
        UTC统一
        会话标注
        质量检查
      研究层
        因子库
        Forward Returns
        IC/RankIC
        分桶分析
        Decay
        OOS验证
      回测层
        研究向量化回测
        成本模型
        订单级适配骨架
      注册与门控
        Dataset Registry
        Factor Registry
        Strategy Registry
        Deploy Gate
        Runtime Gate
      使用入口
        Notebook
        CLI
        最小FastAPI
      技术栈
        Python 3.12
        DuckDB
        Parquet
        PostgreSQL
        sqlite(开发态)
        Prefect
        Backtrader
    第2轮
      宏观与日历
      因子维护
      因子监测
      跨资产上下文
    第3轮
      调度强化
      Monitoring
      Paper Trading
      生产骨架
    第4轮
      执行适配器
      容量评估
      偏离检测
      执行质量分析
    第5轮
      新闻事件
      LSEG Workspace
      高级参考数据
      完整生产化
```

## 阅读顺序

建议按下面顺序看：

1. 先看第 1 轮
2. 再看第 2-5 轮升级路线
3. 最后回到 `spec.md` 看细节定义

## 使用方式

- 当需要讨论“现在先做什么”时，先看 `plan.md`
- 当需要讨论“某个模块应该长什么样”时，先看 `spec.md`
- 当需要快速理解整体框架时，先看这份思维导图
