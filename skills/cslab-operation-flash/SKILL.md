---
name: cslab-operation-flash
description: Use when developing a domain/operation module that inherits Flash and needs TP, TVF, PVF, bubble-point, dew-point, energy-duty, LLE, or VLLE flash calculations.
---

# Flash 子类闪蒸计算

本 Skill 面向 AI 开发继承 `domain.operation.Flash.Flash` 的流程单元。它定义
`Flash` 的公共调用契约、算法口径、结果回写和能量计算复用方式。

部署环境可能只有 Python 3.7 的 `.pyd` 编译模块。公共 API 优先以
`domain/operation/Flash.pyi` 为准：该存根从同目录 `Flash.py` 生成，声明可调用
方法、参数、稳定结果字段及返回形态。本 Skill 说明流程口径和模板；遇到参数名、
可选参数或结果字段问题，先查 `.pyi`，不要猜测。

不要读取、验证、反编译、monkey patch 编译模块，也不要调用双下划线私有迭代辅助函数。

## Stub 查询规则

1. 先读取 `domain/operation/Flash.pyi`，按类 `Flash` 查找目标公共方法。
2. `@overload` 中 `Instantiation=False` 是元组返回；`Instantiation=True` 是
   `FlashResults` 返回。业务模块需要回写状态时，优先后者。
3. 仅 `.pyi` 声明的方法可视为跨 `.py/.pyd` 部署的稳定调用面；不要依赖未声明的
   实例字段、内部 helper 或双下划线方法。
4. `.pyi` 与当前调用模板冲突时，停止猜测并以目标版本已验证的公共接口更新 `.pyi`；
   不得通过探测、反编译或 monkey patch `.pyd` 解决。
5. `.pyi` 不替代坐标系规则：`ZI/K0/x/y` 仍为活跃组分局部坐标，`SkipIndex` 仍为
   全组分坐标。

## 继承边界

```text
MethodH <- MethodLV <- Flash <- 业务单元
```

已有继承示例包括 `Flow`、`Feed`、`FUG`、`RBatch` 和 `MESH_Comm`。

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

子类只调用公共 `flash_*`、`get_H_LV_JB`、`get_duty_by_flash`、`phy_prop` 等方法。
不要复制或重写 `Flash` 内部的 K 值迭代、Rachford-Rice 求根、泡露点求根或 `A` 修正算法。

## 闪蒸前的组成准备

闪蒸使用活跃组分局部向量 `ZI`，并附带全组分坐标下的 `SkipIndex`。

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(
    np.asarray(LVXI_mol, dtype=float)
)
```

调用约束：

1. `ZI` 是一维、非负、已归一化的活跃组分摩尔分率。
2. `SkipIndex=self.Is0` 是原全组分坐标的跳过索引。
3. `len(ZI) + len(SkipIndex)` 应对应全组分数。
4. `K0`、`LXI_mol`、`VXI_mol` 等相组成也必须使用相同活跃组分局部坐标。
5. 子类不应再次切片模型参数；`Flash -> MethodLV -> MethodH` 会通过子 `PropertyPackage` 处理上下文。

## 算法口径

常规气液闪蒸的算法结构固定为：

1. `GetPs_P(T, P, ZI, SkipIndex)` 计算基础相平衡常数。
2. 以非理想修正 `A` 构造：
   ```text
   K_i = GetPs_P_i(T, P, ZI) * A_i
   ```
3. 以 Rachford-Rice 型方程求汽化率或内层未知状态变量：
   ```text
   sum(z_i * (1 - K_i) / (1 + VF * (K_i - 1))) = 0
   ```
4. 更新并归一化两相组成：
   ```text
   x_i = z_i / (1 + VF * (K_i - 1))
   y_i = K_i * x_i
   ```
5. 调用 `get_A(T, P, XI=x, YI=y, ...)` 更新非理想修正。
6. 迭代至 `A` 与前一轮值在 `DOA` / `abs_DOA` 容差内收敛。

外层更新策略：

| 参数 | 含义 |
|---|---|
| `iterative_method="Wegstein"` | 默认加速迭代；连续流程优先使用 |
| `iterative_method="Partial"` | 固定部分松弛 |
| `iterative_method="Direct"` | 不做外层松弛 |
| `iteration_factor` | 初始松弛因子，常用 0.3 |
| `DOA` | 相对收敛容差 |
| `abs_DOA` | 绝对收敛容差 |
| `K_time` | 最大迭代次数 |

纯组分、全零组成、泡点外单液相、露点外单气相等情况已有历史边界分支。子类应接受框架结果，不要强制改为双相解。

## 公共闪蒸接口

| 已知条件 | 公共方法 | 标准返回，`Instantiation=False` |
|---|---|---|
| `T, P, z` | `flash_TP` | `VF, x, y, K` |
| `T, VF, z` | `flash_TVF` | `P, x, y, K` |
| `P, VF, z` | `flash_PVF` | `T, x, y, K` |
| 任意两项 `T/P/VF` | `flash_TPVF` | `T, P, VF, x, y, K` |
| `P, z` 泡点 | `flash_BubT` | `T_bub, y, K` |
| `P, z` 露点 | `flash_DewT` | `T_dew, x, K` |
| `T, z` 泡点 | `flash_BubP` | `P_bub, y, K` |
| `T, z` 露点 | `flash_DewP` | `P_dew, x, K` |
| 压力、热负荷、z | `flash_DP` | 反求温度后的 `T, P, VF, x, y, K` |
| 温度、热负荷、z | `flash_DT` | 反求压力后的 `T, P, VF, x, y, K` |
| 比焓差、定压、z | `flash_HP` | 温度、相态及相组成解 |
| 液液平衡 | `LLE` / `LLE_T` | 两液相分裂结果 |
| 汽液液平衡 | `VLLE` / `VLLE_PE` | 三相平衡结果 |

当 `Instantiation=True` 时，主闪蒸与泡露点接口返回 `FlashResults`。稳定字段为：

```text
T, P, VF, ZI, LXI_mol, VXI_mol, K, A, SkipIndex
```

业务模块需要存储闪蒸状态时，优先使用 `Instantiation=True`。

## 热负荷闪蒸

参数和完整可选初值见 `Flash.pyi` 的 `flash_DP` / `flash_DT`。两者均使用：

| 参数 | 含义 | 单位 |
|---|---|---|
| `FHin` | 入口总焓流 | J/s（W） |
| `F_mol` | 出口总摩尔流量 | kmol/s |
| `target_duty` | 指定热负荷 | J/s（W） |
| `ZI` | 活跃组分进料摩尔组成 | 无量纲 |

已知压力与热负荷，反求温度时使用 `flash_DP`：

```python
result = self.flash_DP(
    FHin=self.Fin.FH,
    F_mol=self.Fin.F_mol,
    target_duty=self.Duty,
    P=self.P_in,
    ZI=self.XI_mol_in,
    T0=self.T0,
    VF0=self.GasRat0,
    K0=self.K0,
    BubT=self.BubT,
    DewT=self.DewT,
    BubK=self.BubK,
    DewK=self.DewK,
    BubT0=self.BubT0,
    DewT0=self.DewT0,
    BubK0=self.BubK0,
    DewK0=self.DewK0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)
self.T = result.T
```

已知温度与热负荷，反求压力时使用 `flash_DT`：

```python
result = self.flash_DT(
    FHin=self.Fin.FH,
    F_mol=self.Fin.F_mol,
    T=self.T,
    target_duty=self.Duty,
    ZI=self.XI_mol_in,
    VF0=self.GasRat0,
    P0=self.P0,
    K0=self.K0,
    BubP=self.BubP,
    DewP=self.DewP,
    BubK=self.BubK,
    DewK=self.DewK,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)
self.P_in = result.P
```

两种热负荷闪蒸完成后，统一用本 Skill 的 TP 回写字段模板写回
`T/P_in/GasRat/XI_mol_in/LXI_mol/VXI_mol/K`。

## 业务规格标志

`TP_BaseOn`、`Te_BaseOn`、`Pe_BaseOn`、`DP_BaseOn`、`DT_BaseOn` 是 `Flash`
的只读 property，详情见 `Flash.pyi`。它们由 `Input_type1` 和 `Input_type2` 的
中文规格组合动态判断，不是根据 `T/P/GasRat/Duty` 是否为 `None` 自动置位：

| 标志 | `Input_type1/2` 的无序组合 | 对应求解 |
|---|---|---|
| `TP_BaseOn` | `温度` + `压力` | `flash_TP` |
| `Te_BaseOn` | `温度` + `汽化率` | `flash_TVF` |
| `Pe_BaseOn` | `压力` + `汽化率` | `flash_PVF` |
| `DP_BaseOn` | `压力` + `热负荷` | `flash_DP` |
| `DT_BaseOn` | `温度` + `热负荷` | `flash_DT` |

不要把历史 `Flow.flashdp()` / `Flow.flashdt()` 的辅助方法名作为物理条件依据：
其名称与实际调用的 `flash_DT` / `flash_DP` 相反。新模块按上述物理名称直接调用。

## 标准 TP 闪蒸与结果回写

`Flow` 风格的模块应按以下顺序调用：

```python
def run_tp_flash(self):
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

    self.T = result.T
    self.P_in = result.P
    self.GasRat = result.VF
    self.XI_mol_in = result.ZI
    self.LXI_mol = result.LXI_mol
    self.VXI_mol = result.VXI_mol
    self.K = result.K
    self.Is0 = result.SkipIndex
    return result
```

`self.XI_mol_in` 是进料组成；`self.LXI_mol` 是液相组成；`self.VXI_mol` 是气相组成。
不要将其中任一个全组分向量与 `self.Is0` 混用。

## TVF、PVF 与统一分派

已知温度和汽化率，求压力：

```python
result = self.flash_TVF(
    T=self.T,
    VF=self.GasRat,
    ZI=self.XI_mol_in,
    P0=self.P0,
    K0=self.K0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)
self.P_in = result.P
```

已知压力和汽化率，求温度：

```python
result = self.flash_PVF(
    P=self.P_in,
    VF=self.GasRat,
    ZI=self.XI_mol_in,
    T0=self.T0,
    K0=self.K0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)
self.T = result.T
```

业务仅需要根据给定的两个 `T/P/VF` 自动选择求解器时：

```python
result = self.flash_TPVF(
    T=self.T,
    P=self.P_in,
    VF=None,
    ZI=self.XI_mol_in,
    SkipIndex=self.Is0,
    Instantiation=True,
)
```

只传入 `T/P/VF` 中任意两个有效状态变量，第三项必须为 `None`。例如上例是
已知 `T/P`、求 `VF`；不要同时传三个值，也不要把三个都设为未知。

## 泡点与露点

```python
self.BubT, y_bub, self.BubTK = self.flash_BubT(
    P=self.P_in,
    ZI=self.XI_mol_in,
    T0=self.BubT0,
    K0=self.BubTK0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
)

self.DewT, x_dew, self.DewTK = self.flash_DewT(
    P=self.P_in,
    ZI=self.XI_mol_in,
    T0=self.DewT0,
    K0=self.DewTK0,
    SkipIndex=self.Is0,
    DOA=self.DOA,
    K_time=self.K_time,
)
```

需要定温泡露点压力时，对应使用 `flash_BubP` 和 `flash_DewP`，并传递 `P0`、`K0`。

## 初值复用与失效条件

相邻流程迭代、时间步或撕裂流股中，状态变化较小时应复用：

```text
K0, VF0, T0, P0, BubT0, DewT0, BubTK0, DewTK0
```

以下情况必须清空或不传旧初值：

1. 方法包变更。
2. `SkipIndex` 变更。
3. 活跃组分数或组成列坐标变更。
4. 组成、温度、压力发生显著跳变。
5. 上一步求解未收敛或产生非有限结果。

不要将不同活跃组分坐标系下的 `K` 直接复用。

## 全组分结果恢复

`Comp_filter` 生成的 `Is0` / `Not0` 用于分别标识全组分中的零组分与活跃组分。
业务结果需要从活跃局部向量恢复到全组分坐标时，使用：

```python
from domain.math.mathmethod import Comp_restore

full_values = Comp_restore(values, self.Is0, self.Not0)
```

`values` 必须是活跃组分局部坐标的向量；`Is0` 和 `Not0` 都是原全组分坐标索引。
不要对 `FlashResults.LXI_mol`、`VXI_mol` 或 `K` 先按 `Is0` 二次切片再恢复。

## 焓与热负荷

不要在子类重复实现单相/两相焓选择。闪蒸完成后优先调用：

```python
self.H_mol, self.HL_mol, self.HV_mol = self.get_H_LV_JB(
    T=self.T,
    P=self.P_in,
    VF=self.GasRat,
    LXI_mol=self.LXI_mol,
    VXI_mol=self.VXI_mol,
    SkipIndex=self.Is0,
)
```

再计算相流量、焓流量：

```python
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

已知入口焓流与目标热负荷、需要反求出口状态时，优先使用 `flash_DP` 或 `flash_HP`；
不要在新模块外层手写温度扫描或有限差分闪蒸循环。

## LLE 与 VLLE

仅在业务模型明确需要液液分层或汽液液三相平衡时调用：

```python
lle_result = self.LLE(
    T=self.T,
    P=self.P_in,
    ZI=self.XI_mol_in,
    key_comp=key_comp,
    SkipIndex=self.Is0,
    DT=self.DT,
    DOA=self.DOA,
    K_time=self.K_time,
)
```

不要用 `LLE` 或 `VLLE` 替代正常的两相 `flash_TP`。涉及液液分裂时，应保持各液相组成、
液相分率和总物料衡算在同一活跃组分坐标系内。

## 禁止事项

1. 不调用 `__get_P`、`__get_T`、`__get_BubT`、`__get_DewT` 等私有求根函数。
2. 不复制 `GetPs_P`、`get_A`、Rachford-Rice 或 Wegstein 迭代逻辑。
3. 不将多工况数组直接传给 `flash_*`。这些求解器是单工况迭代接口。
4. 不把全组分组成传给带 `SkipIndex` 的闪蒸接口。
5. 不对主闪蒸返回的 `T/P/VF/K/x/y` 失败静默使用 `np.nan_to_num` 伪造有效相态。
   已确认零相流的派生物性后处理可按邻近模块历史口径有限化，但必须不掩盖闪蒸或
   物性失败，并保留受控告警路径。
6. 不依赖源码存在；不读取、修改、探测或反编译 `.pyd` 模块。
