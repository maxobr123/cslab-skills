---
name: cslab-operation-phy-prop
description: Use when developing CSLAB domain/operation code that uses the unified inherited phy_prop interface for scalar or matrix enthalpy, density, heat capacity, entropy, Gibbs energy, vapor pressure, fugacity, and other supported properties without reading or implementing property internals.
---

# 业务物性调用

本 Skill 指导开发人员从 `Flash` 子类或已有 operation 基类调用 `phy_prop`。开发任务是
选择正确属性、准备状态与组成、处理返回值，不是开发 `MethodH`、`MethodLV`、EOS、
活度系数、纯物性关联式或混合规则。

本 Skill 同时承担 `phy_prop` 的业务公开接口和属性目录契约。开发环境即使只有编译后的
`domain/method`，也只依赖本文，不读取、探测或重建 `MethodH`、`MethodLV`、EOS、
活度系数、纯物性关联式和混合规则。闪蒸及能量组合契约使用
`cslab-operation-flash`。

## 唯一物性入口

业务层只调用：

```python
self.phy_prop(
    Property=None,
    T=None,
    P=None,
    V=None,
    XI=None,
    XI_mol=None,
    SkipIndex=None,
    MixMode=1,
)
```

`phy_prop` 同时承担标量与矩阵输入。标量状态走标量计算；`T/P` 为数组或组成是二维
矩阵时，统一入口自动进入矩阵路径。业务代码不直接调用 `phy_propArray`、
`CalculateArray`、Property 类、EOS、Phase 或活度模型对象。

## 调用层级

按业务目标选择最高层的现有能力：

| 目标 | 首选调用 |
|---|---|
| 完整流股状态和一组展示属性 | 已有 `Flow.flow_prop(...)` 工作流 |
| 单个纯组分或混合物属性 | `self.phy_prop(...)` |
| 多个严格配对的独立物性工况 | 数组参数调用 `self.phy_prop(...)` |
| 相平衡状态 | `self.flash_*` |
| 闪蒸后的总/分相摩尔焓 | `self.get_H_LV_JB(...)` |
| 焓流 | `self.get_H_F_LV_JB(...)` |
| 相对入口的净热负荷 | `self.get_duty_by_flash(...)` |

不要为计算一个业务属性而独立构造 Property、EOS、MethodH 或 MethodLV 对象。不要把
纯组分属性手工加权冒充包含实际混合规则的 `_MIX` 属性。

## 基本接口

```python
self.phy_prop(
    Property="DS_L_MIX",
    T=self.T,
    P=self.P_in,
    XI_mol=self.LXI_mol,
    SkipIndex=self.Is0,
)
```

公共参数：

| 参数 | 规则 |
|---|---|
| `Property` | 框架属性代码，区分大小写 |
| `T` | K；单工况为标量，多工况为一维数组 |
| `P` | Pa；只在属性需要或现有调用契约使用时传入 |
| `V` | 仅 `P_MIX` 等明确需要摩尔体积的属性使用 |
| `XI` / `XI_mol` | 二选一，不得同时给出 |
| `SkipIndex` | 完整项目组分坐标中的跳过索引 |
| `MixMode` | 兼容性选项；新混合物计算不靠它替代 `_MIX` |

业务模块通常已有摩尔组成字段，应优先沿用其 `XI_mol` 命名。不要在同一个调用中同时
传 `XI` 和 `XI_mol`，也不要为了满足看似可能的参数而伪造压力、体积或组成。

## 组成坐标

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(
    np.asarray(full_xi_mol, dtype=float)
)
```

- `self.Is0` 是全局跳过索引，只作为 `SkipIndex` 使用。
- `self.XI_mol_in`、`self.LXI_mol`、`self.VXI_mol` 是活跃局部组成。
- 传非空 `SkipIndex` 时，组成的最后一维必须等于活跃组分数。
- 不在业务层二次切片 CAS、MW、方法参数或二元参数。
- 对外输出组分向量时用项目已有的 `Comp_restore` 恢复完整坐标。

保留完整共享 `Data`，通过 `Method_bag + SkipIndex` 使用相应组分子系统。不要为二元、
纯组分或局部子系统破坏性裁剪共享 `Data`。

## 相存在性

只有相实际存在时才计算该相物性。先初始化不存在相的业务结果，再按 `GasRat` 分支：

```python
self.DensityL_mol = 0.0
self.DensityV_mol = 0.0

if self.GasRat < 1.0:
    self.DensityL_mol = self.phy_prop(
        Property="DS_L_MIX",
        T=self.T,
        P=self.P_in,
        XI_mol=self.LXI_mol,
        SkipIndex=self.Is0,
    )

if self.GasRat > 0.0:
    self.DensityV_mol = self.phy_prop(
        Property="DS_V_MIX",
        T=self.T,
        P=self.P_in,
        XI_mol=self.VXI_mol,
        SkipIndex=self.Is0,
    )
```

同样规则适用于 `H_*_MIX`、`S_*_MIX`、`CP_*_MIX`、`G_*_MIX` 和传递性质。
`VF=0` 时不要调用气相属性，`VF=1` 时不要调用液相属性。

## 权威属性与常量表

执行物性任务前按需读取以下引用文件：

- [`references/property-catalog.md`](references/property-catalog.md)：`phy_prop` 的 79 个
  注册属性、含义、必需参数、单位及标量/矩阵返回形态。
- [`references/public-constants.md`](references/public-constants.md)：项目热力学、数学及
  供应商附属常量的含义、数值、单位和引用路径。

这两个表是对应定义的唯一权威来源。正文及其他 operation Skill 不再复制属性目录、
属性单位、返回形态或公共常量数值；发现冲突时以表格为准。新增或修正接口时先核对源码
注册与公开契约，再更新表格，不根据类名、文件名或编译模块内容推测可调用属性。

## 能量计算

单独研究某一相或塔板属性时可直接调用 `H_L_MIX` 或 `H_V_MIX`。完整流程闪蒸后的
相焓、总焓和 duty 应复用 Flash helper：

```python
self.H_mol, self.HL_mol, self.HV_mol = self.get_H_LV_JB(
    T=self.T,
    P=self.P_in,
    VF=self.GasRat,
    LXI_mol=self.LXI_mol,
    VXI_mol=self.VXI_mol,
    SkipIndex=self.Is0,
)

self.FV_mol, self.FL_mol = self.get_F_LV_JB(
    F_mol=self.F_mol,
    VF=self.GasRat,
)

self.FH, self.FHL, self.FHV = self.get_H_F_LV_JB(
    F_mol=self.F_mol,
    FL_mol=self.FL_mol,
    FV_mol=self.FV_mol,
    H_mol=self.H_mol,
    HL_mol=self.HL_mol,
    HV_mol=self.HV_mol,
)
```

不要在业务层重写两相焓选择，也不要因已有 `H_L`/`H_V` 就默认简单加权等价于
`H_L_MIX`/`H_V_MIX`。

## Flow 工作流与属性代码

已有 `Flow.flow_prop` 适用于“给定流股输入并获得完整状态及展示属性”的场景。必须区分：

- `DS_L_MIX` 是底层 `phy_prop` 属性代码。
- `"摩尔密度"` 等是 `Flow.flow_prop(calculate_list=...)` 的业务请求名称。
- `DensityL_mol` 等是 Flow 实例字段。
- `"Mole density"` 等是平台结果中的 `unitType`。

这些词汇不能互换。开发新单元前，应从目标 Flow 类或相邻业务单元确认其
`calculate_list` 名称和结果字段；不要从属性代码猜中文展示键。

## 多工况矩阵

数组输入仍调用唯一公开入口 `phy_prop`，由其自动进入矩阵路径。不要直接调用
`phy_propArray` 或内部属性类的 `CalculateArray`，也不要为新批量功能写逐工况标量循环。

```python
def calculate_vapor_enthalpy_cases(self, t_cases, p_cases, y_cases):
    t_arr = np.asarray(t_cases, dtype=float)
    p_arr = np.asarray(p_cases, dtype=float)
    y_arr = np.asarray(y_cases, dtype=float)

    if t_arr.ndim != 1 or p_arr.shape != t_arr.shape:
        raise ValueError("T and P must be paired one-dimensional cases")
    if y_arr.ndim != 2 or y_arr.shape[0] != t_arr.shape[0]:
        raise ValueError("XI rows must match the number of cases")

    return self.phy_prop(
        Property="H_V_MIX",
        T=t_arr,
        P=p_arr,
        XI_mol=y_arr,
        SkipIndex=self.Is0,
    )
```

硬性规则：

1. `T.shape == P.shape == (case_count,)`，同一下标是一组配对工况，不生成笛卡尔积。
2. 混合组成 `XI.shape == (case_count, active_component_count)`。
3. 框架不自动广播标量、不重复组成、不归一化数组、不转换完整坐标到局部坐标。
4. 固定组成必须由调用方显式 `repeat`/`tile` 成二维矩阵。
5. 纯组分向量通常返回 `(case_count, active_component_count)`。
6. 混合标量通常返回 `(case_count,)`。
7. `GAMMAS`、`PHI_*_MIX` 等混合向量返回 `(case_count, active_component_count)`。
8. 闪蒸 `flash_*` 是单工况迭代接口，不能接收这些矩阵。

`Henry`、`DC`、`CP_INF`、`S_INF` 不作为本 Skill 的标准矩阵接口使用。

## 体积与 P_MIX

`VOL_L`、`VOL_V`、`VOL_L_MIX`、`VOL_V_MIX` 的公开返回单位为
`m3/kmol`，数值上等于 `L/mol`。`P_MIX` 的 `V` 参数使用相同单位，因此这些
体积结果可直接传入 `P_MIX`，业务层不得额外乘或除 `1e3`。具体参数与返回规则以
[`references/property-catalog.md`](references/property-catalog.md) 为准。

## 错误处理

- 调用前校验有限的 T/P、组成 shape、非负性和归一化。
- 物性失败时保留诊断并走 `feedback`/受控失败，不返回看似有效的默认值。
- `np.nan_to_num` 只能用于已确认有效相态后的有限派生展示值，并必须保留告警；不能
  掩盖闪蒸或主物性失败。
- 不通过反射、源码内部方法或 `.pyd` 探测发现属性。

## 完成检查

- 选择了正确调用层级，没有重复 Flash 能量组合。
- 属性代码存在于目录，输入和单位匹配。
- `XI`/`XI_mol` 只给一个，局部列与 `SkipIndex` 匹配。
- 不存在相没有被调用。
- 标量和矩阵 shape 没有混用或隐式广播。
- 输出字段、展示名和 `unitType` 没有与属性代码混淆。
- 体积与 `P_MIX.V` 均按权威属性表的 `m3/kmol` 契约传递。
