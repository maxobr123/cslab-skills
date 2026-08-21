---
name: cslab-operation-phy-prop
description: Use when developing CSLAB domain/operation code that uses the unified inherited phy_prop interface for scalar or matrix enthalpy, density, heat capacity, entropy, Gibbs energy, vapor pressure, fugacity, and other supported properties without reading or implementing property internals.
---

# 业务物性调用

本 Skill 只指导 operation 业务代码通过继承得到的统一 `phy_prop` 接口选择和计算物性。
业务代码不开发或绕过 `MethodH`、`MethodLV`、Property、EOS、Phase、活度系数、
纯物性关联式和混合规则。

## 开发边界

1. 单个属性和严格配对的多工况属性都只调用 `self.phy_prop(...)`。
2. 不直接调用 `phy_propArray`、`CalculateArray` 或内部算法对象，不独立构造物性对象。
3. 不读取、反编译、反射或试探编译实现；只使用本 Skill 参考文件声明的公共契约。
4. 不把纯组分属性手工加权冒充 `_MIX` 属性，不在业务层重写 Flash 相焓组合。
5. 保留共享 `Data`；通过 `Method_bag + SkipIndex` 选择组分子系统，不破坏性裁剪数据。
6. 属性代码、必需参数、单位和返回形态只以 `property-catalog.md` 为准。

通用构造、`feedback` 和模块输出遵循 `cslab-module-contract`；测试方式遵循
`cslab-module-verify`。本 Skill 不重复这些通用规则。

## 最短选择流程

1. 完整流股状态和展示属性使用已有 `Flow.flow_prop(...)`；单个或批量物性工况使用
   `phy_prop(...)`；相平衡使用 `flash_*`。
2. 在[属性目录](references/property-catalog.md)确认属性已注册、必需参数、单位和返回形态。
3. 标量调用读取[公共接口与组成坐标](references/phy-prop-api.md)；涉及相存在性或流程
   能量组合时读取[相与能量规则](references/phase-energy.md)。
4. 任何数组状态或二维组成必须读取[矩阵调用契约](references/matrix-calls.md)，确认严格
   一一对应工况语义和输出 shape。
5. 需要常量时读取[公共常量表](references/public-constants.md)，引用项目常量而不复制数值。

## 按需参考

- [公共接口与组成坐标](references/phy-prop-api.md)：`phy_prop` 签名、参数、标量示例、
  局部/完整组分坐标和 Flow 名称层级。
- [属性目录](references/property-catalog.md)：79 个注册属性的含义、必需参数、单位、
  标量/矩阵返回形态和已知未注册属性；这是属性契约的唯一权威来源。
- [相与能量规则](references/phase-energy.md)：相存在性、相物性计算和 Flash 能量组合路由。
- [矩阵调用契约](references/matrix-calls.md)：配对工况、组成矩阵、广播禁令、返回 shape
  以及非标准矩阵属性。
- [公共常量表](references/public-constants.md)：热力学、数学及供应商常量的含义、数值、
  单位和引用路径；这是公共常量的唯一权威来源。

只读取当前任务需要的参考文件；不得在入口或其他 operation Skill 复制属性目录、单位、
返回形态或常量数值。

## 完成检查

- 调用层级正确，属性代码确实存在于权威目录。
- 必需参数、单位、组成坐标与 `SkipIndex` 一致，`XI`/`XI_mol` 只给一个。
- 不存在相未被调用，Flow 展示名与底层属性代码没有混用。
- 标量与矩阵 shape 没有混用、隐式广播或隐式归一化。
- 体积和 `P_MIX.V` 按属性目录的同一单位契约传递。
