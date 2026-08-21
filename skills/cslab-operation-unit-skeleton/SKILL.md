---
name: cslab-operation-unit-skeleton
description: Use when implementing or modifying a steady CSLAB domain/operation business unit Run() that consumes injected Flow ports and publishes state, outlet Flow, or platform results. Excludes dynamic modules and thermodynamic algorithm implementation.
---

# CSLAB 稳态业务单元入口

本 Skill 只负责 `domain/operation/` 稳态业务单元的编排：读取注入端口，调用已有算法，
完成业务衡算并把结果发布给真实消费者。它不实现闪蒸、物性或其他热力学算法，也不适用于
dynamic 模块。

开发交付物只能是 `.py` 源文件；`.pyd/.so` 是运行依赖，不属于开发文件。依赖只有编译
产物时，按 Skill 公开契约调用，不读取、修改、反射、试探或反编译编译模块。

## 必须先确认的契约

编码前从模板详情、开发人员负责范围内的可读 `.py`、同族已验证契约和开发者确认中建立：

1. 实际基类、构造器注入参数、`startFun` 和 `Run()` 消费方式。
2. 输入/输出 Flow 的参数名、方向、相语义和是否必需。
3. 输入规格、实例状态、模板输出属性及其单位和消费者。
4. 入口成功/失败返回是否被控制器消费，错误码采用哪个模块号段。
5. 是否确实具有 Flash、Vessel、ReactionBase 或 `Public_F_P` 等继承能力。

不得根据类名猜测 MRO、端口或 `Duty`/`duty` 别名；Flow 由框架创建并注入，业务单元不得
静默构造替代端口。模板未声明的新变量按 `cslab-module-develop` 的后台配置门禁处理。

## 必读资料

- 每次 operation 开发都读取
  [`references/operation-variables.md`](references/operation-variables.md)。它是变量名、含义、
  单位、组分坐标及专用字段范围的唯一事实源；本文件和其他 reference 不重复变量表。
- 构造器注入、`startFun`、`feedback`、中文源码文档、通用数值保护、返回值和最小实现读取
  [`cslab-module-contract`](../cslab-module-contract/SKILL.md)，本 Skill 不重新定义。
- 使用 Flash 时读取 `cslab-operation-flash`；使用 `phy_prop` 时读取
  `cslab-operation-phy-prop`，不得在业务单元中复制算法。
- 模板确认属于 FlashTank 家族时，再读取
  [`cslab-operation-flashtank`](../cslab-operation-flashtank/SKILL.md)；其他单元不得套用其
  `FFin/FDout/FWout`、MRO、容器或反应字段。

## Run 核心阶段

`Run()` 保持以下执行顺序，方法是否拆分以目标模块复杂度为准：

1. 校验已确认的端口、规格、流量、组成和状态输入。
2. 准备完整/活跃组分坐标、业务输入和有效暖启动。
3. 调用继承的公开算法，校验完整结果并形成待提交状态。
4. 完成物料、相流量、能量及已配置的可选业务计算。
5. 全部成功后一次提交实例状态和输出 Flow，再按消费者契约返回。

先算后提交。失败时不得留下半更新实例状态、污染复用的输出 Flow 或保留失效暖启动。
快照必须复制可变数组；恢复时保持原 Flow 对象身份。

## 本族不可破坏的边界

- Flow 对外组成使用完整项目坐标；Flash/物性内部使用活跃局部坐标加全局 `SkipIndex`。
  `Comp_filter` 产生的跳过索引和保留索引必须成对保存，发布前用 `Comp_restore` 恢复。
- 不裁剪共享 `Data`，不在业务层切片 CAS、MW、方法参数或二元参数。
- 无反应、无侧线的分离或换热单元默认满足总物料衡算；任何流量变化必须有明确物理来源。
- `VF=0/1` 时不得计算或发布不存在相的有效物性；复用的输出端口必须清空不存在相旧值。
- 所有对外输出均由消费者驱动：平台 `result`、模板实例属性和下游 Flow 是三个独立通道。
  只写已核实被前端、落库、控制器或下游节点消费的通道，不构造无用结果或占位方法，
  也不得遗漏真实消费者。
- 稳态 operation 只有在控制器消费时才返回结构化 `result`。动态模块不得套用本 Skill 的
  稳态返回或 Flow 提交范式，应使用 `cslab-dynamic-module`。

## 按需读取

- 单元含 TP/TVF/PVF/duty 规格、组成过滤、暖启动、相焓或状态回滚时，读取
  [`references/flash-specification-run.md`](references/flash-specification-run.md)。
- 单元需要发布分相/总体 Flow、计算公用工程或组织多通道输出时，读取
  [`references/flow-output-and-utility.md`](references/flow-output-and-utility.md)。

只读取当前任务需要的 reference；Flash 方法签名和物性属性目录仍分别以对应 Skill 为准。

## 完成检查

- 模板、同族证据和实现中的端口、字段、规格及 `startFun` 一致。
- 完整/活跃组分坐标没有混用，暖启动与当前方法包和 `SkipIndex` 一致。
- 物料与能量口径清楚，零流量、单相边界和失败事务得到处理。
- 只提交有消费者的实例属性、Flow 和返回结果，失败路径不污染外部状态。
- 交付文件为 `.py`，没有复制 Flash/物性算法或臆造编译模块接口。
