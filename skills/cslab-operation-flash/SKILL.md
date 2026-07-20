---
name: cslab-operation-flash
description: Use when developing a domain/operation module that inherits Flash and needs TP, TVF, PVF, bubble-point, dew-point, energy-duty, LLE, or VLLE flash calculations.
---

# Flash 子类闪蒸计算

本 Skill 面向 AI 开发继承 `domain.operation.Flash.Flash` 的流程单元。它定义
`Flash` 的公共调用契约、算法口径、结果回写和能量计算复用方式。

部署环境可能只有 Python 3.7 的 `.pyd` 编译模块。本 Skill 中列出的继承关系、
公共方法、参数、返回值和模板就是稳定 API。直接使用；不要读取、验证、反编译、
monkey patch 编译模块，也不要调用双下划线私有迭代辅助函数。

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
| `P, duty, z` 定压热负荷 | `flash_DP` | 温度、相态及相组成解 |
| `T, duty, z` 定温热负荷 | `flash_DT` | 压力、相态及相组成解 |
| 焓、定压 | `flash_HP` | 温度、相态及相组成解 |
| 液液平衡 | `LLE` / `LLE_T` | 两液相分裂结果 |
| 汽液液平衡 | `VLLE` / `VLLE_PE` | 三相平衡结果 |

当 `Instantiation=True` 时，主闪蒸与泡露点接口返回 `FlashResults`。稳定字段为：

```text
T, P, VF, ZI, LXI_mol, VXI_mol, K, A, SkipIndex
```

业务模块需要存储闪蒸状态时，优先使用 `Instantiation=True`。

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

已知入口焓流与目标热负荷、需要反求出口状态时，优先使用 `flash_DP` / `flash_DT` /
`flash_HP`；不要在新模块外层手写温度扫描或有限差分闪蒸循环。

### 热负荷闪蒸 flash_DP 与 flash_DT

已知压力与目标热负荷,反求温度、汽化率与相组成:

```python
result = self.flash_DP(
    FHin=self.FFin.FH,          # 入口焓流
    F_mol=self.FFin.F_mol,      # 进料摩尔流量
    target_duty=self.duty,      # 目标热负荷
    P=self.P_in,
    ZI=self.XI_mol,
    T0=self.T0, K0=self.K0, VF0=self.VF0,
    SkipIndex=self._Is0,
    Instantiation=True,
    DOA=self.DOA, K_time=self.K_time,
)
self.T = result.T
```

已知温度与目标热负荷,反求压力、汽化率与相组成:

```python
result = self.flash_DT(
    FHin=self.FFin.FH,
    F_mol=self.FFin.F_mol,
    T=self.T,
    target_duty=self.duty,
    ZI=self.XI_mol,
    VF0=self.VF0, P0=self.P0, K0=self.K0,
    SkipIndex=self._Is0,
    Instantiation=True,
    DOA=self.DOA, K_time=self.K_time,
)
self.P_in = result.P
```

说明:

1. 两个接口以 `Instantiation=True` 返回 `FlashResults`(字段同上文稳定字段表);
   业务模块一律用 `Instantiation=True`,`Instantiation=False` 的返回形态未验证。
2. `FHin` 是入口流股焓流(`FFin.FH`),与 `target_duty` 一起构成能量衡算基准;
   不要改用自算相焓拼装替代。
3. 签名取自真实调用方(FlashTank 稳态源码);若实际参数不符,以运行时报错为准
   回查,不要凭猜测增删参数。

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
5. 不对主闪蒸失败静默使用 `np.nan_to_num` 伪造有效相态。
6. 不依赖源码存在；不读取、修改、探测或反编译 `.pyd` 模块。
