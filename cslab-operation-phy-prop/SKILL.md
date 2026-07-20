---
name: cslab-operation-phy-prop
description: Use when developing a domain/operation module that inherits Flash and needs phy_prop or phy_propArray to calculate thermodynamic properties, including enthalpy, density, heat capacity, entropy, Gibbs energy, vapor pressure, and multi-case matrix properties.
---

# Flash 子类物性调用

本 Skill 面向 AI 开发 `domain/operation/` 中的业务模块。调用方是继承
`Flash` 的模块实例，例如 `Flow`、`Feed`、`FUG`，而不是独立创建
`MethodH`、`MethodLV` 或属性计算类。

部署环境可能只有 Python 3.7 的 `.pyd` 编译模块。本 Skill 中列出的公共继承关系、
方法、参数、结果形态和模板就是稳定契约。直接使用它们；不要读取、验证、反编译、
monkey patch 编译模块，也不要调用双下划线私有方法。

## 继承与初始化

继承链固定为：

```text
MethodH <- MethodLV <- Flash <- Flow / Feed / FUG / 新业务模块
```

新模块必须继承 `Flash`，并先完成父类初始化。父类会建立 `Data`、方法包、
物性 `PropertyPackage`、迭代参数和基础相态字段。

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

不要绕过 `super().__init__`。初始化完成后，可直接在子类中调用：

```python
self.phy_prop(...)
self.phy_propArray(...)
self.flash_TP(...)
```

## 模块状态与坐标系

参考 `Flow.Determine_the_phase_state()` 的状态流。必须严格区分两个坐标系：

| 坐标系 | 字段/含义 | 使用位置 |
|---|---|---|
| 全组分坐标 | `self.Is0`，被跳过或零组成组分的全局索引 | 仅作为 `SkipIndex=self.Is0` 传入 |
| 活跃组分坐标 | `self.XI_mol_in`、`self.LXI_mol`、`self.VXI_mol` | 作为 `XI` 或 `XI_mol` 传给物性/闪蒸 |
| 全组分结果 | 模块最终对外结果 | 必要时用既有 `Comp_restore` 恢复 |

典型准备过程：

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(np.asarray(LVXI_mol))
```

规则：

1. `self.Is0` 的索引永远指向原全组分列表。
2. `self.XI_mol_in`、`self.LXI_mol`、`self.VXI_mol` 必须只包含未跳过的活跃组分。
3. 传 `SkipIndex=self.Is0` 时，绝不能再传全组分长度的组成向量。
4. 不要在业务模块中根据 `self.Is0` 二次切片 CAS、MW、方法、纯组分参数或二元参数；当前 `PropertyPackage` 会处理子系统上下文。
5. 若业务结果必须恢复到全组分坐标，使用项目已有的 `Comp_restore`，不要修改物性计算内部结果。

## phy_prop 公共接口

```python
self.phy_prop(
    Property=<属性代码>,
    T=<K>,
    P=<Pa 或 None>,
    V=<仅特定属性需要的摩尔体积>,
    XI=<活跃组分组成>,
    XI_mol=<活跃组分摩尔组成>,
    SkipIndex=self.Is0,
    MixMode=1,
)
```

基本规则：

1. `Property` 使用框架属性代码，例如 `H_L`、`H_V`、`H_L_MIX`、`VP`、`BP`、`DS_L_MIX`。
2. `T` 单位为 K；`P` 单位为 Pa。
3. `XI` 与 `XI_mol` 只能给一个。流程模块中的组成通常是摩尔分率，优先使用现有的 `XI_mol` 状态字段。
4. `MixMode=0` 仅用于需要保留纯组分逐组分结果的历史业务逻辑。不能用它替代正确的 `_MIX` 混合物属性。
5. `V` 只传给明确以摩尔体积为输入的属性，例如 `P_MIX`。
6. 单工况使用标量 `T/P`。不要为了形式统一而把普通单点调用包装成数组。

## 属性总表与调用约定

本节是新业务功能直接调用 `self.phy_prop` 的属性参考。先根据物理目标选属性，
再按表中“所需输入”提供参数。除特别标注外，均应带上当前模块的
`SkipIndex=self.Is0`。

### 输入和结果符号

| 符号 | 说明 |
|---|---|
| `T` | 温度，K |
| `P` | 压力，Pa |
| `x` | 当前活跃组分局部坐标下的摩尔组成；可传 `XI` 或 `XI_mol`，二者不可同时传 |
| `V` | 混合物摩尔体积，m3/kmol；仅 `P_MIX` 必需 |
| `S` | `SkipIndex=self.Is0`；无跳过组分时可为 `None` |
| `n` | 当前活跃组分数 |
| `c` | 批量工况数 |

标量接口的结果形态：

| 结果标记 | 标量调用返回 | 矩阵调用返回 |
|---|---|---|
| `纯向量` | `(n,)`，每个活跃组分一个值 | `(c, n)` |
| `混合标量` | 单个 `float` | `(c,)` |
| `混合向量` | `(n,)`，每个活跃组分一个值 | `(c, n)` |
| `Henry 向量` | `(h,)`，仅当前活跃亨利组分，`h` 可小于 `n` | 当前不作为标准矩阵接口 |

“所需输入”表示计算口径真正依赖的输入。历史实现可能接受额外兼容参数；AI 不要
为满足旧函数签名而伪造物理输入。压力不影响的纯关联式可不传 `P`；若模块已经有
`P`，传入同一工况压力是安全的。

矩阵能力边界：下表的“矩阵调用返回”是已接入标准数组链路的属性应遵守的结果形态。
`Henry`、`DC`、`P`、`CP_INF`、`S_INF` 当前不在标准矩阵化计划中；新模块对它们只
使用标量 `phy_prop`，不要把多工况数组传给这些属性。`P_MIX` 的矩阵路径需要严格的
`T.shape == V.shape == (c,)` 与 `x.shape == (c, n)`。

### 纯组分基础、热容与传递性质

| 属性 | 所需输入 | 标量结果 | 单位 | 物性说明 |
|---|---|---|---|---|
| `CPIG` | `T, S` | 纯向量 | J/(kmol*K) | 理想气体定压热容 |
| `CP_DEP_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 气相定压热容偏离项 |
| `CP_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 气相定压热容，理想项加偏离项 |
| `CP_DEP_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 液相定压热容偏离项 |
| `CP_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 液相定压热容 |
| `CP_S` | `T, S` | 纯向量 | J/(kmol*K) | 固相定压热容 |
| `CP_INF` | `T, S` | 纯向量 | J/(kmol*K) | 无限稀释热容/方法包定义的纯组分热容 |
| `S_INF` | `T, S` | 纯向量 | J/(kmol*K) | 无限稀释标准熵/方法包定义熵项 |
| `CV_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 气相定容热容 |
| `CV_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 液相定容热容 |
| `ST` | `T, S` | 纯向量 | N/m | 纯组分表面张力 |
| `TC_L` | `T, P, S` | 纯向量 | W/(m*K) | 纯组分液相导热系数 |
| `TC_V` | `T, P, S` | 纯向量 | W/(m*K) | 纯组分气相导热系数 |
| `VS_L` | `T, S` | 纯向量 | Pa*s | 纯组分液相动力粘度 |
| `VS_V` | `T, P, S` | 纯向量 | Pa*s | 纯组分气相动力粘度 |
| `DS_L` | `T, P, S` | 纯向量 | kmol/m3 | 纯组分液相摩尔密度 |
| `DS_V` | `T, P, S` | 纯向量 | kmol/m3 | 纯组分气相摩尔密度 |
| `DS_S` | `T, P, S` | 纯向量 | kmol/m3 | 纯组分固相摩尔密度 |
| `VOL_L` | `T, P, S` | 纯向量 | m3/kmol | 纯组分液相摩尔体积，通常为 `1 / DS_L` |
| `VOL_V` | `T, P, S` | 纯向量 | m3/kmol | 纯组分气相摩尔体积 |
| `MDS_L` | `T, P, S` | 纯向量 | kg/m3 | 纯组分液相质量密度，通常为 `DS_L * MW` |
| `MDS_V` | `T, P, S` | 纯向量 | kg/m3 | 纯组分气相质量密度，通常为 `DS_V * MW` |
| `VP` | `T, S` | 纯向量 | Pa | 饱和蒸气压 |
| `BP` | `P, S`；`T` 可作初值 | 纯向量 | K | 给定压力下的纯组分沸点，反解 `VP(T)=P` |
| `EOV` | `T, S` | 纯向量 | J/kmol | 纯组分蒸发焓/汽化焓关联式 |
| `DC` | `T, S` | 纯向量 | 无量纲 | 纯组分介电常数 |
| `P` | 仅按当前历史方法包定义传参 | 纯向量 | Pa | 历史纯组分压力属性；新业务不要用它代替 `VP`、`P_MIX` 或流程压力 |

### 纯组分相态热力学函数

| 属性 | 所需输入 | 标量结果 | 单位 | 物性说明 |
|---|---|---|---|---|
| `H_I_V` | `T, S` | 纯向量 | J/kmol | 理想气体焓，相对框架参考态 |
| `H_I_L` | `T, P, S` | 纯向量 | J/kmol | 理想液相焓，通常由理想气体焓与汽化焓关系组成 |
| `H_I_S` | `T, S` | 纯向量 | J/kmol | 固相理想焓 |
| `H_DEP_V` | `T, P, S` | 纯向量 | J/kmol | 气相焓偏离项 |
| `H_DEP_L` | `T, P, x(活度模型时), S` | 纯向量 | J/kmol | 液相焓偏离项 |
| `H_V` | `T, P, S` | 纯向量 | J/kmol | 纯组分气相摩尔焓 |
| `H_L` | `T, P, x(活度模型时), S` | 纯向量 | J/kmol | 纯组分液相摩尔焓 |
| `H_S` | `T, S` | 纯向量 | J/kmol | 纯组分固相摩尔焓 |
| `S_I_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 理想气体熵，含压力基准项 |
| `S_I_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 理想液相熵 |
| `S_DEP_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 气相熵偏离项 |
| `S_DEP_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 液相熵偏离项 |
| `S_V` | `T, P, S` | 纯向量 | J/(kmol*K) | 纯组分气相摩尔熵 |
| `S_L` | `T, P, x(活度模型时), S` | 纯向量 | J/(kmol*K) | 纯组分液相摩尔熵 |
| `G_I_V` | `T, P, S` | 纯向量 | J/kmol | 理想气体 Gibbs 自由能 |
| `G_I_L` | `T, P, x(活度模型时), S` | 纯向量 | J/kmol | 理想液相 Gibbs 自由能 |
| `G_DEP_V` | `T, P, S` | 纯向量 | J/kmol | 气相 Gibbs 偏离项 |
| `G_DEP_L` | `T, P, x(活度模型时), S` | 纯向量 | J/kmol | 液相 Gibbs 偏离项 |
| `G_V` | `T, P, S` | 纯向量 | J/kmol | 纯组分气相 Gibbs 自由能 |
| `G_L` | `T, P, x(活度模型时), S` | 纯向量 | J/kmol | 纯组分液相 Gibbs 自由能 |
| `PHI_V` | `T, P, x(电解质修正时), S` | 纯向量 | 无量纲 | 纯组分气相逸度系数 |
| `PHI_L` | `T, P, x(活度模型/电解质时), S` | 纯向量 | 无量纲 | 纯组分液相逸度系数 |

### 混合物热力学与传递性质

`_MIX` 不表示“纯组分加权平均”。它表示当前方法包定义的混合物属性，应在有
实际混合规则、EOS 或活度系数贡献时优先使用。

| 属性 | 所需输入 | 标量结果 | 单位 | 物性说明 |
|---|---|---|---|---|
| `CP_L_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 液相混合物定压热容 |
| `CP_V_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 气相混合物定压热容 |
| `CV_L_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 液相混合物定容热容 |
| `CV_V_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 气相混合物定容热容 |
| `DS_L_MIX` | `T, P, x, S` | 混合标量 | kmol/m3 | 液相混合物摩尔密度 |
| `DS_V_MIX` | `T, P, x, S` | 混合标量 | kmol/m3 | 气相混合物摩尔密度 |
| `MDS_L_MIX` | `T, P, x, S` | 混合标量 | kg/m3 | 液相混合物质量密度 |
| `MDS_V_MIX` | `T, P, x, S` | 混合标量 | kg/m3 | 气相混合物质量密度 |
| `VOL_L_MIX` | `T, P, x, S` | 混合标量 | m3/kmol | 液相混合物摩尔体积 |
| `VOL_V_MIX` | `T, P, x, S` | 混合标量 | m3/kmol | 气相混合物摩尔体积 |
| `ST_MIX` | `T, P, x, S` | 混合标量 | N/m | 混合物表面张力 |
| `TC_L_MIX` | `T, P, x, S` | 混合标量 | W/(m*K) | 液相混合物导热系数 |
| `TC_V_MIX` | `T, P, x, S` | 混合标量 | W/(m*K) | 气相混合物导热系数 |
| `VS_L_MIX` | `T, P, x, S` | 混合标量 | Pa*s | 液相混合物动力粘度 |
| `VS_V_MIX` | `T, P, x, S` | 混合标量 | Pa*s | 气相混合物动力粘度 |
| `H_L_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 液相混合物摩尔焓 |
| `H_V_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 气相混合物摩尔焓 |
| `S_L_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 液相混合物摩尔熵 |
| `S_V_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 气相混合物摩尔熵 |
| `G_L_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 液相混合物 Gibbs 自由能 |
| `G_V_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 气相混合物 Gibbs 自由能 |
| `H_EX_L_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 液相过量焓 |
| `H_EX_V_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 气相过量焓 |
| `S_EX_L_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 液相过量熵 |
| `S_EX_V_MIX` | `T, P, x, S` | 混合标量 | J/(kmol*K) | 气相过量熵 |
| `G_EX_L_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 液相过量 Gibbs 自由能 |
| `G_EX_V_MIX` | `T, P, x, S` | 混合标量 | J/kmol | 气相过量 Gibbs 自由能 |
| `GAMMAS` | `T, P, x, S` | 混合向量 | 无量纲 | 液相活度系数 |
| `PHI_L_MIX` | `T, P, x, S` | 混合向量 | 无量纲 | 混合液相每个组分的逸度系数 |
| `PHI_V_MIX` | `T, P, x, S` | 混合向量 | 无量纲 | 混合气相每个组分的逸度系数 |
| `Henry` | `T, P, x, S` | Henry 向量 | 依方法包定义 | 活跃亨利组分在当前溶剂混合物中的亨利系数；不是全部组分向量 |
| `P_MIX` | `T, V, x, S` | 混合标量 | Pa | 按混合 EOS 由温度、摩尔体积和组成反算压力 |

### 直接调用示例

新功能直接求某一混合属性时，按属性表调用，不需要先经过 `Flow` 的焓流或热负荷组合：

```python
self.CPL_mol = self.phy_prop(
    Property="CP_L_MIX",
    T=self.T,
    P=self.P_in,
    XI_mol=self.LXI_mol,
    SkipIndex=self.Is0,
)

self.gamma_l = self.phy_prop(
    Property="GAMMAS",
    T=self.T,
    P=self.P_in,
    XI_mol=self.LXI_mol,
    SkipIndex=self.Is0,
)
```

需要由 `T/V/x` 反算压力时：

```python
pressure = self.phy_prop(
    Property="P_MIX",
    T=self.T,
    V=molar_volume,
    XI_mol=self.XI_mol_in,
    SkipIndex=self.Is0,
)
```

## 优先复用已有组合方法

属性表支持新业务直接调用单项物性；但当目标已经是现成的流程组合问题时，优先使用
`Flash` 公共方法，避免重复实现相态分支、焓流和物料衡算：

| 目标 | 优先复用 |
|---|---|
| 给定 `T/P/z` 求相态与 `x/y/K` | `self.flash_TP(...)` |
| 给定 `T/VF/z` 或 `P/VF/z` 反求状态 | `self.flash_TVF(...)` / `self.flash_PVF(...)` |
| 已知闪蒸结果求相摩尔焓与总摩尔焓 | `self.get_H_LV_JB(...)` |
| 已知相焓与相流量求焓流 | `self.get_H_F_LV_JB(...)` |
| 已知入口焓流与闪蒸状态求热负荷 | `self.get_duty_by_flash(...)` |

只有当上述组合方法不能表达新业务目标时，才根据属性表自行组合 `phy_prop` 结果。

## 可复制的模块模板

### 混合相密度

在已完成闪蒸、`self.LXI_mol` / `self.VXI_mol` 已就绪时调用：

```python
def calculate_phase_density(self):
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

### 相焓、焓流与热负荷

优先复用 `Flash` 已有的公共方法，而不是在子类复制相焓分支：

```python
def calculate_energy(self, inlet_flow=None):
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

    if inlet_flow is not None:
        self.duty = self.FH - inlet_flow.FH
```

需要在指定入口焓流下直接求热负荷时，使用：

```python
duty = self.get_duty_by_flash(
    FHin=FHin,
    F_mol=self.F_mol,
    T=self.T,
    P=self.P_in,
    VF=self.GasRat,
    LXI_mol=self.LXI_mol,
    VXI_mol=self.VXI_mol,
    SkipIndex=self.Is0,
)
```

### 需要逐组分纯物性时

仅在业务确实要保存或再计算每个组分的属性时使用纯组分属性。不要将纯组分加权结果误当成混合物模型结果。

```python
self.HLXI_mol = self.phy_prop(
    Property="H_L",
    T=self.T,
    P=self.P_in,
    SkipIndex=self.Is0,
)

self.HVXI_mol = self.phy_prop(
    Property="H_V",
    T=self.T,
    P=self.P_in,
    SkipIndex=self.Is0,
)
```

如果当前相实际是纯组分，可显式按相组成加权：

```python
self.HL_mol = np.sum(self.HLXI_mol * self.LXI_mol)
```

混合相应优先使用 `H_L_MIX` / `H_V_MIX`，或直接使用上面的 `get_H_LV_JB`。

## 多工况矩阵物性

`phy_prop` 会在 `T/P` 为数组或 `XI` 为二维数组时自动进入矩阵路径。模块优先继续调用
`self.phy_prop(...)`；不要直接调用内部属性类的 `CalculateArray`。

```python
def calculate_vapor_enthalpy_cases(self, t_cases, p_cases, y_cases):
    t_arr = np.asarray(t_cases, dtype=float)
    p_arr = np.asarray(p_cases, dtype=float)
    y_arr = np.asarray(y_cases, dtype=float)

    # t_arr.shape == p_arr.shape == (case_count,)
    # y_arr.shape == (case_count, active_component_count)
    return self.phy_prop(
        Property="H_V_MIX",
        T=t_arr,
        P=p_arr,
        XI_mol=y_arr,
        SkipIndex=self.Is0,
    )
```

矩阵调用硬性规则：

1. `T.shape == P.shape == (case_count,)`，每个下标是一个独立工况。
2. 混合物 `XI.shape == (case_count, active_component_count)`。
3. 纯组分属性通常返回 `(case_count, active_component_count)`；混合物标量通常返回 `(case_count,)`；`GAMMAS`、`PHI_L_MIX` 等逐组分属性返回 `(case_count, active_component_count)`。
4. 框架不会自动广播 `T/P/XI`，不会自动重复组成，也不会归一化正式数组输入。
5. 同一组成计算多个工况时，业务模块负责用 `np.repeat` 或 `np.tile` 形成二维组成矩阵。
6. `SkipIndex` 仍使用同一个全局索引集合；组成矩阵的列只对应活跃组分。
7. 矩阵接口只用于独立物性批量计算。`Flash` 的 `flash_*` 求解器是单工况迭代接口，不能把多工况数组直接传给它。

## 禁止事项

1. 不独立构造 `MethodH`、`MethodLV`、Property 类或 EOS/活动系数对象来绕过 `Flash` 上下文。
2. 不混用全组分向量与活跃组分向量。
3. 不在业务模块二次按 `SkipIndex` 切片物性模型输入数据。
4. 不用纯组分属性和 `MixMode` 替代有实际混合规则的 `_MIX` 属性。
5. 不把矩阵接口实现成业务模块中的逐工况 `for` 循环调用标量 `phy_prop`。
6. 不依赖源码存在；不读取、修改、探测或反编译 `.pyd` 模块。
