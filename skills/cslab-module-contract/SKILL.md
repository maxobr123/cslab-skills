---
name: cslab-module-contract
description: Use when writing any CSLab algorithm module. Defines the platform-wide constructor injection, startFun, consumer-driven outputs, feedback, Chinese documentation, numerical protection, and minimal-source boundaries; family-specific algorithms belong to their family Skill.
---

# CSLab 模块通用契约

本 Skill 只拥有所有模块族共享的平台契约。设备变量、方程、继承方法和族专用返回形式由
对应族 Skill 定义，不在这里重复。

## 必须遵守的边界

1. 模板属性、节点和入口依赖严格名称匹配；`__init__` 形参及 `startFun` 不是自由命名。
2. 模板值直接注入，框架不做单位换算；算法内部和模板默认值均使用已确认的 SI 口径。
3. 未连接的 FLOW/Energy 节点可为 `None`，访问前必须判空。
4. 只实现已经核实的消费者：入口返回、同名实例属性和出口节点相互独立，不机械补齐。
5. `feedback` 由框架动态注入；模块不自定义它，不用 `print` 代替平台诊断。
6. 算法开发和交付对象只能是 `.py`；`.pyd/.so` 是编译依赖，不读取、探测或反编译。
7. 每个保留的方法、参数、状态和结果字段必须有契约、物理、消费者、异常隔离、复用、
   性能或测试价值；没有依据的代码删除或内联。

## 按需读取

不要默认加载全部资料。只读取当前任务涉及的 reference：

| 当前任务 | 必须读取 |
|---|---|
| 修改构造形参、模板属性/节点、`startFun`、返回值、实例属性、出口或 `feedback` | [`references/runtime-contract.md`](references/runtime-contract.md) |
| 新建/修改算法源码、补注释、删除冗余方法或执行源码审计 | [`references/source-documentation.md`](references/source-documentation.md) |
| 涉及物性、衡算、迭代、积分、优化、矩阵或状态更新的数值保护 | [`references/numerical-boundary-protection.md`](references/numerical-boundary-protection.md) |

族专用信息按任务加载：

- 稳态 operation：`cslab-operation-unit-skeleton`；
- Flash/物性调用：`cslab-operation-flash`、`cslab-operation-phy-prop`；
- FlashTank：`cslab-operation-flashtank`；
- 动态生命周期：`cslab-dynamic-module`；
- 测试方法：`cslab-module-verify`；
- 后台模板事实：`cslab-modulet-api`。

## 最短执行流程

1. 从当前模板和控制器确认构造注入、真实入口及输出消费者。
2. 读取上表中与改动相符的 reference，建立单位、坐标、返回和失败契约。
3. 编写最小必要源码；中文文档必须解释实际物理口径、参数、状态修改和失败行为。
4. 对可恢复数值边界只做保护，不把模板缺失或接口错误伪造成合法输入。
5. 使用 `scripts/audit_module_source.py` 预检，再按 `cslab-module-verify` 做真实入口验证。

## 完成门禁

- 模板形参与入口方法严格同名；入口除框架确认的特殊签名外按控制器要求调用。
- 每个输出都有真实消费者；无消费者时不构造 `result`、空字典或占位字段。
- 数值保护保留守恒和上一有效状态，不抛错、不虚构默认值。
- 所有说明性注释为中文，复杂方法的方程、变量、单位、步骤和状态副作用完整。
- 目标源码由本地 `.py` 实际加载，未把编译文件当成开发文件或完成证据。
