# Dynamic V4 调度与设备入口

## 每次先核实

读取当前工程运行入口、控制器映射、目标模板 `startFun` 和控制器 `algorithm_call()`。
控制器升级或工程使用其他映射时，重新记录入口、参数、返回消费者、实时推送和错误处理，
不能把本文 V4 事实盲目套到其他版本。

当前仓库已核实链路：

1. `chemicalLib/runServerDynamic_v2.py` 导入 `chemicalLib/runServer_v2.py`，后者使用
   `calculateControl_v2.py`；`callow_way="dynamic"` 映射 V4 主控制器，动态子进程
   `dynamic_dynamic` 映射 V4 子控制器。
2. 主、子进程最终均调用控制器小写 `run()`；它不是设备模块入口。
3. V4 主控制器调用模板 `startFun`；子控制器固定无参调用设备 `RunDynamic()`。
4. `DRun()` 是 V1 历史追加调用，V4 已废弃。旧
   `runServerDynamic.py -> runServer.py -> calculateControl.py` 链路不能作为 V4 验收依据。

当前项目目录可能重命名或并存多个运行库，上述路径仅是已核实样本。测试时仍须搜索当前
工程的真实入口和映射，不假定路径固定。

## 入口矩阵

| 控制器角色/模板条件 | 控制器方法 | 设备入口 | 参数 | 说明 |
|---|---|---|---|---|
| V4 主进程普通模板 | `run()` | 模板 `startFun`，通常 `Run()` | 无参 | 每轮一次，不追加 DRun |
| V4 主进程 `startFun="RunOde"` | `run()` | `RunOde(ts, dt)` | 控制器时间和有效步长 | 特殊 ODE 分派 |
| V4 动态子进程 | `run()` | `RunDynamic()` | 无参 | 忽略模板 startFun |
| 历史 V1 | `run()` | startFun 后可能追加 `DRun(...)` | 历史参数 | 只维护锁定 V1 的工程 |

名称严格区分：控制器 `run()`/`run_dynamic()` 与设备 `Run()`、`RunDynamic()`、
`RunOde()` 不同；当前源码未发现设备 `dynamic_run()`。入口缺失可能被控制器当作成功空结果，
所以验收必须证明真实方法被调用且状态随时间变化。

## 步长

普通设备在 `Run()` 或 `RunDynamic()` 单步中读取 `self.Data.PGV["DT"]`，每步只读取一次。
不得新增外部步长契约。`Data`、`PGV` 或 `DT` 缺失，或 DT 不是有限正数时，保持上一状态和
出口，不抛错、不反馈、不采用默认步长。

`RunOde(ts, dt)` 只用于模板和控制器已确认的特殊路径，技术方案必须解释其时间和步长语义，
不能推广到普通设备。

## 延迟初始化

- `__init__` 只读取同名构造注入的属性和节点。
- 构造后挂载的液位、温度、尺寸等模板初值在首次入口延迟读取。
- 内部状态初值来源和优先级由开发者确认，例如模板状态、累计量或快照恢复值。
- 内部积分状态与展示属性避免多份漂移，只在成功提交时集中同步。
