---
name: cslab-operation-flash
description: Use when developing CSLAB domain/operation code that calls inherited Flash APIs for TP, TVF, PVF, duty, bubble/dew, LLE, phase-flow, enthalpy, or duty calculations without reading or probing compiled implementations.
---

# Flash 业务调用

本 Skill 只指导 `domain/operation/` 业务模块选择和调用继承得到的 Flash 公共能力。
业务代码负责规格编排、流股状态和业务结果，不实现 K 值、EOS、活度系数、
Rachford-Rice、泡露点求根或其他物性算法。

## 开发边界

1. 通过继承 `Flash` 或已有 operation 基类获得能力，不单独构造物性算法对象。
2. 沿用目标类已验证的 MRO，并把基类要求的 `Data`、`Method_bag` 和迭代参数传给
   `super().__init__`；不为直接继承 `Flash` 改变现有继承关系。
3. 只调用参考文件声明的公共方法；未声明接口视为没有业务契约，不猜测参数试调用。
4. 不读取、反编译、反射、monkey patch 或试探 `.pyd`，不调用双下划线方法。
5. 所有业务参数使用关键字传递。常规 `flash_*` 是单工况接口；多工况物性转用
   `phy_prop`，不得把矩阵传给 Flash。
6. 结果必须完整校验后一次性发布；失败结果不得污染出口或继续作为暖启动值。

构造、`feedback` 和模块输出遵循 `cslab-module-contract`；测试入口和源码直载遵循
`cslab-module-verify`。本 Skill 不重复这些通用规则。

## 最短选择流程

1. 明确已知规格、待求状态、入口焓流、净热负荷以及是否要求液液分层。
2. 从[相平衡接口](references/flash-equilibrium-api.md#求解器选择)匹配唯一求解器；
   不根据字段是否为 `None` 自行设置规格标志。
3. 若涉及 `flash_DP`、`flash_DT`、相流量、相焓、焓流或 duty，读取
   [热负荷与能量接口](references/flash-duty-energy-api.md)。
4. 准备局部组成、`SkipIndex`、返回模式、状态校验或暖启动时，读取
   [状态、坐标与失败契约](references/flash-state-contract.md)。
5. 只有相实际存在时才发布相状态；可复用出口对象必须清除不存在相的旧值。

## 按需参考

- [相平衡接口](references/flash-equilibrium-api.md)：TP、TVF、PVF、TPVF、泡点、露点和
  LLE 的参数、元组返回顺序及求解器选择。
- [热负荷与能量接口](references/flash-duty-energy-api.md)：DP/DT、相流量、相焓、焓流
  和净热负荷 helper 的参数、返回和调用顺序。
- [状态、坐标与失败契约](references/flash-state-contract.md)：结果对象字段、单位、
  shape、局部/完整组分坐标、校验回写、相边界、暖启动和 Flash 专有失败规则。
- [operation 变量表](../cslab-operation-unit-skeleton/references/operation-variables.md)：
  Flow 及扩展模块变量的含义和单位的唯一权威来源。

只读取当前任务需要的参考文件；不得把参考内容重新复制回本入口或其他 Skill。

## 完成检查

- 求解器与物理规格相符，参数、单位和返回模式符合对应接口参考。
- 局部组成、完整项目坐标和 `SkipIndex` 一致。
- 元组顺序或结果对象字段使用正确，结果先校验后完整回写。
- `VF=0/1` 和 LLE 相存在性得到显式处理。
- 相流量、焓流和 duty 复用公开 helper，失败不会留下脏状态或失效暖启动。
