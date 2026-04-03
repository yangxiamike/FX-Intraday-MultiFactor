# Real Data Fixtures

本目录用于保存从 Massive/Polygon 免费档 API 获取并固化的真实小样本。

用途：

- 作为默认离线测试输入
- 作为 `demo` 的默认数据来源
- 作为标准化、质量检查、回测与门控的可复现样本

约束：

- 只保存第 1 轮所需的最小真实样本
- 不保存生成假行情
- 样本窗口必须落在 Massive/Polygon 免费档可获取的最近 `2 年` 范围内

生成方式：

```powershell
set FXMF_POLYGON_API_KEY=你的key
fxmf fetch-api-sample
```

如果当前仓库里还没有真实 fixture，相关离线 workflow 测试会明确跳过，并提示先执行上面的命令。
