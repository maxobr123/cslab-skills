---
name: cslab-operation-flashtank
description: Use only for a verified steady FlashTank-family domain/operation unit whose template uses the family-specific vessel, Flash specification, reaction, utility, or FFin/FDout/FWout contracts. Do not apply it to unrelated operation or dynamic modules.
---

# FlashTank 家族入口

本 Skill 只定义经模板或同族运行证据确认的稳态 FlashTank（平衡闪蒸罐）业务边界。Heater、
Pump、普通分离器以及 dynamic 设备不得套用本族 MRO、端口、容器、反应或输出字段。

开发交付物只能是 `.py`；`.pyd/.so` 不是开发文件。编译依赖只按公开 Skill 契约调用，
不得读取、修改、反射、试探或反编译。

## 加载顺序

1. 先读取 [`cslab-operation-unit-skeleton`](../cslab-operation-unit-skeleton/SKILL.md)，执行
   稳态 `Run()`、事务和消费者发布的通用规则。
2. 必须读取
   [`operation-variables.md`](../cslab-operation-unit-skeleton/references/operation-variables.md)。
   它是变量名、单位、组分坐标、FlashTank/Vessel/Utility/Data 字段的唯一事实源。
3. 构造器注入、`startFun`、`feedback`、中文源码文档、数值保护和返回契约读取
   [`cslab-module-contract`](../cslab-module-contract/SKILL.md)。
4. Flash 方法签名读取 `cslab-operation-flash`；物性入口读取
   `cslab-operation-phy-prop`，本族代码不得复制这些算法。

## 家族确认门禁

编码前必须从目标模板、开发人员负责范围内可读 `.py` 或已验证同族契约确认：

- 输入和输出端口是否确为 `FFin/FDout/FWout`，各自的相语义及是否还有 `DutyIn`。
- 两组输入规格、实际分派标志、状态字段大小写以及暖启动字段。
- Flash、Vessel、Utility、ReactionBase 能力的真实来源和 `super().__init__` 契约。
- 模板输出属性、容器/设计字段、反应 ID、错误码和所有输出消费者。

不能从类名、旧示例或变量词汇表反推某个能力已经存在。表外新变量走
`cslab-module-develop` 的后台配置确认流程；模板落库属性必须严格同名。

## Run 核心阶段

FlashTank 的 `Run()` 仍遵守稳态先算后提交，并按以下阶段组织：

1. 接收能量流规格，校验 `FFin`、输入条件、流量和完整组成。
2. 判断暖启动有效性，过滤组成并保存成对的跳过/保留索引。
3. 按已确认的 `*_BaseOn` 调用继承 Flash 方法，校验并回写完整闪蒸状态。
4. 计算相流量、能量、容器派生量，以及模板已启用的反应和公用工程。
5. 全部成功后恢复完整坐标，提交模板实例属性、`FDout/FWout`、能量流和被消费的结果。

## FlashTank 专有边界

- 只组合模板确认的基类，不重新实现闪蒸迭代、相焓、Rachford-Rice、容器或反应算法。
- `Comp_filter` 后至 `Comp_restore` 前的相组成和 K 值均为活跃局部坐标，并始终传当前
  全局 `SkipIndex`；方法包、活跃组分或索引变化后禁止复用旧 `K0`。
- `VF=0/1` 时不存在相的组成置零用于清除旧输出，不作为有效相态参与计算。
- 反应仅在模板确认 `ReactionBase` 且 `RList` 非空时执行，并遵守已验证的入口流股口径；
  不得擅自回改闪蒸主状态。
- 构造器只初始化模板、框架或下游消费者确实读取的输出属性。没有消费者的结果、占位方法、
  Vessel/Utility/Reaction 字段一律不构造。
- 稳态 `result` 仅在控制器消费时生成；dynamic 罐不得复用本 Skill 的返回格式、状态推进或
  时间步语义，应使用 `cslab-dynamic-module`。

## 按需读取

- 需要确认 MRO、构造参数、模板输出初始化、输入规格分派或暖启动时，读取
  [`references/construction-and-dispatch.md`](references/construction-and-dispatch.md)。
- 需要反应调用、分相出口、能量流反写或多通道字段提交时，读取
  [`references/reaction-and-outputs.md`](references/reaction-and-outputs.md)。
- 规格输入校验、Flash 结果校验、相能量和事务回滚还应按需读取
  [`flash-specification-run.md`](../cslab-operation-unit-skeleton/references/flash-specification-run.md)。

## 完成检查

- 目标已由模板或同族证据确认为 FlashTank，且 MRO、端口和字段均有消费者证据。
- 规格分派、完整/活跃坐标、暖启动、单相边界及失败事务正确。
- 反应、容器和 Utility 只在模板启用时执行，没有复制基类算法。
- 实例属性、`FDout/FWout`、能量流和入口返回只发布真实消费者需要的内容。
- 交付文件为 `.py`，没有把本族稳态范式扩散到 dynamic 或其他 operation 家族。
