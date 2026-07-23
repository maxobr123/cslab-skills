---
name: cslab-operation-flash
description: Use when developing CSLAB domain/operation code that calls inherited Flash APIs for TP, TVF, PVF, duty, bubble/dew, LLE, phase-flow, enthalpy, or duty calculations.
---

# Flash 业务调用

本 Skill 指导开发人员在 `domain/operation/` 业务模块中调用继承得到的热力学能力。
开发人员只编排公开接口、流股和业务结果，不开发 K 值、EOS、活度系数、
Rachford-Rice、泡露点求根或其他物性算法。

需要确认方法的参数和返回顺序时，读取
[references/flash-api.md](references/flash-api.md)。该参考只列业务调用面，不代表可以
调用同名类的内部 helper。

## 开发边界

1. 业务类通过继承 `Flash` 或已有 operation 基类获得方法，不单独构造物性算法对象。
2. 必须把 `Data`、`Method_bag` 和目标基类要求的迭代参数传给 `super().__init__`。
3. 只调用本文和 API 参考中列出的公共方法。
4. 不读取、反编译、反射、monkey patch `.pyd`，不调用双下划线方法。
5. 缺少已验证契约的接口不得靠猜参数名试调用；优先改用本文覆盖的稳定业务组合。

```python
from domain.operation.Flash import Flash


class MyOperation(Flash):
    def __init__(
        self,
        Data=None,
        Method_bag=None,
        DT=0.01,
        DOA=0.005,
        K_time=100,
        **kwargs
    ):
        super().__init__(
            Data=Data,
            Method_bag=Method_bag,
            DT=DT,
            DOA=DOA,
            K_time=K_time,
        )
```

若目标类继承的是 `Flow`、`Utility_U` 等已有基类，沿用该类经过验证的构造契约，
不要为了直接继承 `Flash` 改变既有 MRO。

## 单位与坐标

| 量 | 单位/约束 |
|---|---|
| `T` | K |
| `P`、`P_in` | Pa |
| `VF`、`GasRat` | 气相摩尔分率，0 到 1 |
| `F_mol`、`FL_mol`、`FV_mol` | kmol/s |
| `H_mol`、`HL_mol`、`HV_mol` | J/kmol |
| `FH`、`FHL`、`FHV`、`FHin`、`target_duty` | J/s，即 W |

闪蒸始终区分两套组分坐标：

- `ZI`、`K0`、`LXI_mol`、`VXI_mol` 是活跃组分局部向量。
- `SkipIndex` 是被过滤组分在完整项目组分表中的全局索引。
- 对外写入 Flow 的组成必须恢复为完整组分坐标。

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(
    np.asarray(full_xi_mol, dtype=float)
)

full_vapor_xi = Comp_restore(self.VXI_mol, self.Is0, self.Not0)
```

调用前检查 `ZI` 一维、非负、和接近 1。传入非空 `SkipIndex` 时，不得同时传完整长度
组成。不得在业务代码中再次切片 CAS、MW、纯物性或二元参数。

## 求解器选择

| 已知业务规格 | 调用 | 求解量 |
|---|---|---|
| `T + P + z` | `flash_TP` | `VF, x, y, K` |
| `T + VF + z` | `flash_TVF` | `P, x, y, K` |
| `P + VF + z` | `flash_PVF` | `T, x, y, K` |
| `P + FHin + duty + z` | `flash_DP` | `T, VF, x, y, K` |
| `T + FHin + duty + z` | `flash_DT` | `P, VF, x, y, K` |
| 定压泡点/露点 | `flash_BubT` / `flash_DewT` | 温度及另一相组成 |
| 定温泡点/露点 | `flash_BubP` / `flash_DewP` | 压力及另一相组成 |
| 液液分层 | `LLE` | 液液分率、两液相组成、`KLL` |

`TP_BaseOn`、`Te_BaseOn`、`Pe_BaseOn`、`DP_BaseOn`、`DT_BaseOn` 由
`Input_type1` 和 `Input_type2` 的中文规格组合判断：

| 标志 | 无序规格组合 |
|---|---|
| `TP_BaseOn` | `温度` + `压力` |
| `Te_BaseOn` | `温度` + `汽化率` |
| `Pe_BaseOn` | `压力` + `汽化率` |
| `DP_BaseOn` | `压力` + `热负荷` |
| `DT_BaseOn` | `温度` + `热负荷` |

不要根据字段是否为 `None` 自行设置这些标志。历史 `Flow.flashdp()` 和
`Flow.flashdt()` 的名称与其内部物理调用相反，新代码必须直接使用 `flash_DP` 和
`flash_DT`。

## 返回模式

常用 `flash_*` 支持两类返回：

- 默认元组模式适合局部计算，必须按 API 参考中的固定顺序解包。
- `Instantiation=True` 返回结果对象，适合需要完整回写状态的业务单元。

结果对象的常规稳定字段为：

```text
T, P, VF, ZI, LXI_mol, VXI_mol, K, A, SkipIndex
```

不要把 `A` 当作 `K`。三相扩展字段只在对应三相接口实际返回时使用。

## 标准状态回写

```python
result = self.flash_TP(
    T=self.T,
    P=self.P_in,
    ZI=self.XI_mol_in,
    SkipIndex=self.Is0,
    VF0=self.GasRat0,
    K0=self.K0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)

required = ("T", "P", "VF", "ZI", "LXI_mol", "VXI_mol", "K", "SkipIndex")
if isinstance(result, str) or not all(hasattr(result, name) for name in required):
    raise RuntimeError(str(result))

vectors = [
    np.asarray(result.ZI, dtype=float),
    np.asarray(result.LXI_mol, dtype=float),
    np.asarray(result.VXI_mol, dtype=float),
    np.asarray(result.K, dtype=float),
]
try:
    values = np.asarray([result.T, result.P, result.VF], dtype=float)
except (TypeError, ValueError):
    raise RuntimeError("flash returned non-real T, P, or VF")
if values.shape != (3,) or not np.all(np.isfinite(values)):
    raise RuntimeError("flash returned an invalid state")
if values[0] <= 0.0 or values[1] <= 0.0 or not 0.0 <= values[2] <= 1.0:
    raise RuntimeError("flash returned nonphysical T, P, or VF")
if any(value.ndim != 1 or value.size != len(self.XI_mol_in) for value in vectors):
    raise RuntimeError("flash returned incompatible component coordinates")
if any(not np.all(np.isfinite(value)) for value in vectors):
    raise RuntimeError("flash returned non-finite component values")
if np.any(vectors[0] < 0.0) or not np.isclose(vectors[0].sum(), 1.0):
    raise RuntimeError("flash returned invalid feed composition")
if values[2] < 1.0 and (
    np.any(vectors[1] < 0.0) or not np.isclose(vectors[1].sum(), 1.0)
):
    raise RuntimeError("flash returned invalid liquid composition")
if values[2] > 0.0 and (
    np.any(vectors[2] < 0.0) or not np.isclose(vectors[2].sum(), 1.0)
):
    raise RuntimeError("flash returned invalid vapor composition")
if np.any(vectors[3] < 0.0):
    raise RuntimeError("flash returned invalid K values")
result_skip = [] if result.SkipIndex is None else list(result.SkipIndex)
expected_skip = [] if self.Is0 is None else list(self.Is0)
if result_skip != expected_skip:
    raise RuntimeError("flash changed SkipIndex unexpectedly")

# Validate first, then publish the new instance state.
self.T = float(values[0])
self.P_in = float(values[1])
self.GasRat = float(values[2])
self.XI_mol_in = vectors[0]
self.LXI_mol = vectors[1]
self.VXI_mol = vectors[2]
self.K = vectors[3]
```

保留调用前生成且已校验相等的 `Is0/Not0`，不要用只有 `SkipIndex`、没有 `Not0` 的
结果对象替换其中一半坐标元数据。回写后处理相边界：`VF <= 0` 时不存在气相，
`VF >= 1` 时不存在液相。下游端口是可复用对象时必须清空不存在相的旧状态，不能简单
跳过写入而留下上次运行结果。

## 热负荷闪蒸

压力加热负荷反求温度：

```python
result = self.flash_DP(
    FHin=self.Fin.FH,
    F_mol=self.F_mol,
    target_duty=self.Duty,
    P=self.P_in,
    ZI=self.XI_mol_in,
    T0=self.T0,
    VF0=self.GasRat0,
    K0=self.K0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)
```

温度加热负荷反求压力时改用 `flash_DT`，传 `T` 和可选 `P0`。`F_mol` 必须是
出口总摩尔流量且不能为零；`target_duty` 是相对 `FHin` 的净热负荷。求解后使用同一套
标准状态校验和回写，不要只写回求解的 `T` 或 `P`。`flash_DT` 在 duty 超出给定温度
下的可达区间时可能返回诊断字符串；必须将其作为受控失败处理，不能访问 `.T`。

## 相流量与能量

闪蒸完成后复用公共组合方法：

```python
self.FV_mol, self.FL_mol = self.get_F_LV_JB(
    F_mol=self.F_mol,
    VF=self.GasRat,
)
self.H_mol, self.HL_mol, self.HV_mol = self.get_H_LV_JB(
    T=self.T,
    P=self.P_in,
    VF=self.GasRat,
    LXI_mol=self.LXI_mol,
    VXI_mol=self.VXI_mol,
    SkipIndex=self.Is0,
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

`get_H_LV_JB` 是相边界安全的组合方法：它根据 `VF` 只计算存在相，不存在相焓保持
为零。因此应传入闪蒸返回的同坐标相组成并调用一次，不要在业务层自行重写相焓分支。

注意 `get_F_LV_JB` 返回气相在前 `(FV_mol, FL_mol)`，而
`get_H_F_LV_JB` 的参数是液相流量在前。调用后者必须使用关键字。

已知入口焓流并已完成出口闪蒸时，用 `get_duty_by_flash` 计算净热负荷，不手工重复
相焓选择。

## 暖启动

同一方法包、同一 `SkipIndex`、相邻状态变化较小时可以复用 `K0`、`VF0`、`T0`、
`P0` 和泡露点初值。以下任一情况必须丢弃旧初值：

1. `Method_bag` 或 `SkipIndex` 改变。
2. 活跃组分数或向量列坐标改变。
3. 状态或组成发生显著跳变。
4. 上一步不收敛、抛出异常或返回非有限值。

## 泡露点与 LLE

泡点返回平衡气相组成，露点返回平衡液相组成。元组模式统一为
`(状态值, 另一相组成, K)`，具体签名见 API 参考。

`LLE` 元组为 `(LLRat, L1XI_mol, L2XI_mol, KLL)`。业务代码必须拒绝 `None`、
`LLRat <= 0`、`LLRat >= 1` 或两液相组成实质相同的伪分层结果。普通 VLE 不得改用
`LLE` 或 `VLLE`。

`flash_HP`、`flash_SatT`、`VLLE_PE` 和历史 `*_Opration`/`simple` 接口不属于本 Skill
推荐的新业务调用面。没有目标版本的已验证调用样例时，不生成这些接口的新代码。

## 失败处理

1. 调用前校验温度、压力、流量、组成和规格是否完整。
2. 捕获项目中已知的输入或收敛异常，保留原异常上下文并调用 `feedback`。
3. 闪蒸失败后清除暖启动值，返回受控失败，不写入出口 Flow。
4. 不对失败的 `T/P/VF/K/x/y` 使用 `np.nan_to_num` 伪造有效状态。
5. 不在外层自行扫描温度、压力或实现有限差分求解来替代公开闪蒸接口。

## 完成检查

- 求解器与物理规格相符。
- 所有参数使用关键字，单位正确。
- 局部组成和全局 `SkipIndex` 匹配。
- 返回模式和解包顺序正确。
- 结果对象先校验类型、有限性、shape 和 `SkipIndex`，再完整回写状态。
- `VF=0/1` 时不存在相得到显式处理。
- 相流量、焓和 duty 使用公共 helper。
- 失败路径不会污染输出流股或保留失效暖启动。
