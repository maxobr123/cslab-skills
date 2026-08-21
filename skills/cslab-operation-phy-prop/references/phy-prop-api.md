# `phy_prop` 公共接口与组成坐标

本文件是 operation 业务层 `phy_prop` 调用签名、参数语义、组成坐标和 Flow 名称层级的
唯一事实源。属性代码、属性参数要求、单位和返回形态以
[属性目录](property-catalog.md)为准。

## 唯一物性入口

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

`phy_prop` 同时承担标量与矩阵输入。标量状态走标量计算；`T/P` 为数组或组成是二维矩阵
时，统一入口自动进入矩阵路径。业务代码不直接调用 `phy_propArray`、`CalculateArray`、
Property 类、EOS、Phase 或活度模型对象。

## 调用层级

| 目标 | 首选调用 |
|---|---|
| 完整流股状态和一组展示属性 | 已有 `Flow.flow_prop(...)` 工作流 |
| 单个纯组分或混合物属性 | `self.phy_prop(...)` |
| 多个严格配对的独立物性工况 | 数组参数调用 `self.phy_prop(...)` |
| 相平衡状态 | `self.flash_*` |
| 闪蒸后的总/分相摩尔焓 | `self.get_H_LV_JB(...)` |
| 焓流 | `self.get_H_F_LV_JB(...)` |
| 相对入口的净热负荷 | `self.get_duty_by_flash(...)` |

不要为一个业务属性独立构造 Property、EOS、MethodH 或 MethodLV 对象。不要把纯组分
属性手工加权冒充包含实际混合规则的 `_MIX` 属性。

## 公共参数

```python
self.phy_prop(
    Property="DS_L_MIX",
    T=self.T,
    P=self.P_in,
    XI_mol=self.LXI_mol,
    SkipIndex=self.Is0,
)
```

| 参数 | 规则 |
|---|---|
| `Property` | 框架属性代码，区分大小写 |
| `T` | K；单工况为标量，多工况为一维数组 |
| `P` | Pa；只在属性需要或现有调用契约使用时传入 |
| `V` | 仅 `P_MIX` 等明确需要摩尔体积的属性使用 |
| `XI` / `XI_mol` | 二选一，不得同时给出 |
| `SkipIndex` | 完整项目组分坐标中的跳过索引 |
| `MixMode` | 兼容性选项；新混合物计算不靠它替代 `_MIX` |

业务模块通常已有摩尔组成字段，应优先沿用 `XI_mol`。不要为满足看似可能的参数而伪造
压力、体积或组成。

## 组成坐标

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(
    np.asarray(full_xi_mol, dtype=float)
)
```

- `self.Is0` 是完整项目坐标中的跳过索引，只作为 `SkipIndex` 使用。
- `self.XI_mol_in`、`self.LXI_mol`、`self.VXI_mol` 是活跃局部组成。
- 传非空 `SkipIndex` 时，组成最后一维必须等于活跃组分数。
- 不在业务层二次切片 CAS、MW、方法参数或二元参数。
- 对外输出组分向量时，用项目已有的 `Comp_restore` 恢复完整坐标。

保留完整共享 `Data`，通过 `Method_bag + SkipIndex` 使用相应组分子系统。不要为二元、
纯组分或局部子系统破坏性裁剪共享 `Data`。

## 主结果有效性

- 调用前校验有限的 `T/P`、组成 shape、非负性和归一化。
- 主物性返回非有限值或不符合目录声明的 shape 时，视为计算失败并保留诊断。
- 不用 `np.nan_to_num` 把失败的主物性伪造成有效值；它只可用于已确认有效状态后的
  有限派生展示值，并且必须保留告警。

## Flow 名称层级

已有 `Flow.flow_prop` 适用于“给定流股输入并获得完整状态及展示属性”的场景。下列词汇
属于不同层级，不能互换：

- `DS_L_MIX`：底层 `phy_prop` 属性代码。
- `"摩尔密度"`：`Flow.flow_prop(calculate_list=...)` 的业务请求名称。
- `DensityL_mol`：Flow 实例字段。
- `"Mole density"`：平台结果中的 `unitType`。

开发新单元前，从目标 Flow 类或相邻业务单元确认 `calculate_list` 名称和结果字段，不从
属性代码猜中文展示键。

## 体积与 `P_MIX`

`VOL_L`、`VOL_V`、`VOL_L_MIX`、`VOL_V_MIX` 的返回单位以及 `P_MIX.V` 的输入单位
只以[属性目录](property-catalog.md)为准。两者可按目录契约直接传递，业务层不得额外乘
或除 `1e3`。
