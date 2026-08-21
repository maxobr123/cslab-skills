---
name: cslab-dynamic-module
description: Use when designing, implementing, modifying, or debugging CSLab domain/dynamic modules. Defines Dynamic V4 device entries, PGV DT ownership, one-step advancement, default classical RK4, lazy state initialization, atomic state/output publication, and dynamic verification boundaries.
---

# CSLab 动态模块契约

本 Skill 只定义 `domain/dynamic/` 共享的调度和状态生命周期，不定义具体设备方程。改变
方程、模型假设或数值方法时先执行 `cslab-module-develop` 的调研和确认门禁；通用注入、
输出、中文文档和数值保护使用 `cslab-module-contract`；测试入口使用
`cslab-module-verify`。

## 动态硬约束

1. 每次开发都从当前工程核实控制器版本、角色、模板 `startFun` 和真实测试入口，不能仅凭
   历史文件名或旧测试推断生命周期。
2. 当前已核实 V4 普通主进程调用模板入口（通常 `Run()`），动态子进程固定调用
   `RunDynamic()`，特殊 ODE 路径调用 `RunOde(ts, dt)`；`DRun()` 是 V1 历史契约。
3. 普通设备每个动态步从 `self.Data.PGV["DT"]` 读取并锁定有限正步长，不新增 `dt` 模板
   属性、构造参数或入口参数，也不使用硬编码默认值。
4. 一个控制器周期只能推进一次状态。入口负责边界快照、单步推进、保护、出口发布和提交；
   RK4 方法只计算候选状态，不直接修改真实状态或出口。
5. 普通常微分模型默认经典显式 RK4。只有刚性、DAE、强不连续、解析更新或经验证的稳定性/
   性能问题才比较替代方法，并由开发者明确确认。
6. 构造后才挂载的模板状态在首次入口延迟初始化；内部积分状态和模板展示属性各有唯一来源，
   在成功提交时集中同步。
7. 候选状态完整保护后才发布出口并提交；失败时恢复出口快照、保留上一已提交状态，不报错、
   不虚构默认状态。干槽、满槽、溢流等按已确认物理关系处理并保持守恒。
8. 没有已核实返回值消费者时，不定义或构造 `result`；实时展示使用同名实例属性，下游使用
   出口节点。

## 按需读取

| 当前任务 | 必须读取 |
|---|---|
| 判断 V4 主/子进程、设备入口、历史 V1 差异或延迟初始化 | [`references/dynamic-v4-runtime.md`](references/dynamic-v4-runtime.md) |
| 设计状态方程、单步推进、RK4、事件、状态保护或输出发布 | [`references/dynamic-step-rk4.md`](references/dynamic-step-rk4.md) |
| 执行源码直载、动态整图、时间序列和边界验证 | [`references/dynamic-verification.md`](references/dynamic-verification.md) 及 `cslab-module-verify` |

不要默认加载全部 reference。具体设备方程、变量、单位、假设和初边值来自开发者确认的技术
方案和当前模板，不得从目标 `.pyd/.so` 反推。

## 最短实现流程

1. 核实控制器角色和设备入口，确认 `Data.PGV["DT"]` 或特殊 `RunOde` 步长来源。
2. 公开状态向量、方程、变量单位、边界、初值、时间层级、RK4 边界处理和输出消费者。
3. 开发者确认后实现状态导数、纯候选 RK4 和一次原子提交。
4. 覆盖静止、正常变化、边界、无效步长和发布失败；连续记录多个时间步。
5. 删除临时观测，确认本地实际加载目标 `.py` 后交付。

## 完成门禁

- V4 新模块未增加 `DRun()`、`run_dynamic()`、`dynamic_run()` 或重复积分入口。
- 普通设备每步只读取一次 `self.Data.PGV["DT"]`，每次入口只推进一个项目步长。
- RK4 阶段时间、状态 shape、单位和边界时间层级一致；事件子步总时长等于项目步长。
- 状态、实例属性和出口在同一时间层级原子发布，失败保持旧状态。
- 无返回消费者时没有结果字典；动态变化由时间序列、守恒和边界采用情况证明。
