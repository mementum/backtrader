# 假数据场景

该目录保存很小的本地假数据和可执行场景，用于在不依赖外部服务的情况下，
快速测试 backtrader 核心对象。

在仓库根目录运行：

```bash
PYTHONPATH=. python3 tests/fake_data/scenarios.py
```

场景覆盖：

- position 更新
- order execution bits 和 pending clone notifications
- trade 生命周期更新
- commission info 计算
- sizer 和 broker commission lookup
- volume fillers
- 基于假 OHLCV 数据的小型 Cerebro 运行
