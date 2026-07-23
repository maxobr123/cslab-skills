---
name: cslab-operation-unit-skeleton
description: Use when implementing a CSLAB domain/operation business unit Run() with injected Flow ports, Flash specification dispatch, phase outlets, heat duty, feedback, utility accounting, and structured results.
---

# CSLAB 业务单元 Run 骨架

本 Skill 用于编排 `domain/operation/` 业务单元，不开发热力学或化工算法。开发人员组合
已有 Flow 端口、继承方法、规格、闪蒸、物性、能量、公用工程和平台输出。

闪蒸方法参数与返回规则使用 `cslab-operation-flash`，物性代码与 shape 使用
`cslab-operation-phy-prop`。

## 先确认目标单元契约

修改或新建单元前，从同一模块族的可读业务源码确认：

1. 实际基类和 `super().__init__` 参数。
2. 构造器注入的输入/输出 Flow 参数名及端口语义。
3. `T`、`P_in`、`GasRat`、`Duty`/`duty` 等目标字段名。
4. `Input_type1`、`Input_type2` 的可用规格。
5. `feedback` 调用形态和错误码号段。
6. `Run()` 的 `(success, result)` 契约和结果字典展示键。
7. 是否确实继承了 `Public_F_P` 等公用工程 API。

不能从类名推测 `Utility_U`、`Vessel`、`ReactionBase` 的 MRO 或方法。`Duty` 与 `duty`
不是通用别名，必须使用目标单元族实际字段。流股由外部创建并注入，业务单元不静默创建
替代输入/输出端口。

需求未指定且没有既有同族模块时，使用以下最小规范命名，避免自行发明端口：

| 新单元类型 | 构造器注入 | 状态/规格字段 | 输出语义 |
|---|---|---|---|
| TP 气液分离器 | `Fin, FVout, FLout, Data, Method_bag` | `T, P_in` | `FVout` 纯气相，`FLout` 纯液相 |
| 压力加 duty 单出口单元 | `Fin, Fout, Data, Method_bag` | `P_in, Duty` | `Fout` 为总体闪蒸后流股 |

这些名称只作为从零开发的规范默认值。需求或既有同族模块给出其他名称时，以明确契约为准。
两个规范模板都应通过继承 `Flash` 或项目已有 Flash-capable 基类取得算法，并保存注入的 Flow，
不能在 `Run()` 内重新构造它们。

## 常用 Flow 字段

| 字段 | 含义 | 单位/坐标 |
|---|---|---|
| `T` | 温度 | K |
| `P_in` | 计算压力 | Pa |
| `P_out` | 下游压力约定 | Pa |
| `F_mol` | 总摩尔流量 | kmol/s |
| `XI_mol` | 对外流股组成 | 完整组分坐标 |
| `FXI_mol` | 组分摩尔流量 | 完整组分坐标，kmol/s |
| `FH` | 总焓流 | W |
| `GasRat` | 气相摩尔分率 | 0 到 1 |

闪蒸内部的 `XI_mol_in`、`LXI_mol`、`VXI_mol` 是活跃组分局部向量。写入下游
Flow 前必须 `Comp_restore(values, Is0, Not0)`。

## Run 五段式

`Run()` 按以下顺序组织：

1. 校验端口、规格、流量、组成和状态输入。
2. 准备完整/活跃组成坐标和业务计算输入。
3. 调用继承的公开算法并完整回写状态。
4. 计算相流量、焓、热负荷及可选公用工程。
5. 所有计算成功后提交输出 Flow，并返回结构化结果。

先算后提交可避免失败计算留下半写入的下游状态。

## 输入校验与受控失败

以下模板中的错误码仅为占位，必须替换为目标模块实际号段：

```python
def _fail(self, message, code):
    self.feedback("error", message, code)
    return False, {}


def Run(self):
    if self.Fin is None:
        return self._fail("缺少入口流股", 40001)
    try:
        inlet_flow = float(self.Fin.F_mol)
    except (TypeError, ValueError):
        return self._fail("入口摩尔流量无效", 40002)
    if not np.isfinite(inlet_flow) or inlet_flow < 0.0:
        return self._fail("入口摩尔流量无效", 40002)
    if self.Fin.XI_mol is None:
        return self._fail("缺少入口组成", 40003)

    # Continue only after all required inputs are valid.
```

若项目惯例不使用 `_fail` helper，可内联反馈和返回。致命校验失败不得沿用历史上
`feedback(error)` 后仍返回 `(True, {})` 的行为，也不得继续写输出流股。

零流量的处理取决于单元物理意义：允许旁路时显式复制安全字段并返回成功；不允许时受控
失败。不能把零流量传给 `flash_DP`/`flash_DT`。

## 组成准备

```python
try:
    full_xi = np.asarray(self.Fin.XI_mol, dtype=float)
except (TypeError, ValueError):
    return self._fail("入口组成无法转换为数值向量", 40004)
if full_xi.ndim != 1 or not np.all(np.isfinite(full_xi)):
    return self._fail("入口组成必须是一维有限向量", 40004)
if full_xi.size != self.Data.Length:
    return self._fail("入口组成长度与项目组分数不一致", 40004)
if np.any(full_xi < 0.0) or full_xi.sum() <= 0.0:
    return self._fail("入口组成必须非负且总和大于零", 40005)

xi_sum = full_xi.sum()
if not np.isclose(xi_sum, 1.0, rtol=1e-6, atol=1e-8):
    return self._fail("入口组成未归一化", 40006)

full_xi = full_xi / xi_sum
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(full_xi)
```

不要裁剪共享 `Data`，不要在业务层切片 CAS、MW 或物性参数。暖启动 K 只有在当前
`SkipIndex` 与旧坐标完全一致时才复用。

无反应、无侧线的分离器或加热/冷却器默认物料守恒，应在规格分派前显式设置
`self.F_mol = inlet_flow`。只有目标业务明确包含反应、排放、添加物流或其他流量变化
时，才能使用不同出口总流量并在物料衡算中说明来源。

热负荷规格还要求入口 `Fin.FH` 为有限值。如果上游没有填充 `FH`，先调用该 Flow 已有
的完整状态/焓计算工作流；没有已验证入口时返回受控失败，不在本单元手工拼纯物性来猜焓流。

## 规格值准备

在调用求解器前，将当前规格需要的状态转换为有限实数并写回规范数值。转换应位于
`Run()` 的受控 `try` 内：

```python
def require_finite_scalar(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("{} must be a real scalar".format(name))
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError("{} must be a real scalar".format(name))
    if not np.isfinite(result):
        raise ValueError("{} must be finite".format(name))
    return result


def prepare_flash_specification_values(self):
    if self.TP_BaseOn or self.Te_BaseOn or self.DT_BaseOn:
        self.T = require_finite_scalar(self.T, "T")
        if self.T <= 0.0:
            raise ValueError("T must be greater than zero K")

    if self.TP_BaseOn or self.Pe_BaseOn or self.DP_BaseOn:
        self.P_in = require_finite_scalar(self.P_in, "P_in")
        if self.P_in <= 0.0:
            raise ValueError("P_in must be greater than zero Pa")

    if self.Te_BaseOn or self.Pe_BaseOn:
        self.GasRat = require_finite_scalar(self.GasRat, "GasRat")
        if not 0.0 <= self.GasRat <= 1.0:
            raise ValueError("GasRat must be between zero and one")

    if self.DP_BaseOn or self.DT_BaseOn:
        self.Duty = require_finite_scalar(self.Duty, "Duty")
```

若目标单元使用小写 `duty`，在此模板中统一替换字段名，不同时维护两个可能分叉的值。
`T0/P0/VF0/K0` 是可选暖启动；复用前同样检查有限性、范围和组分坐标，不合格时直接
设为 `None`，不能让坏初值进入求解器。

## 规格分派

`*_BaseOn` 由 `Input_type1/Input_type2` 的中文规格无序组合产生，不根据状态字段是否
为 `None` 推断：

```python
def run_flash_specification(self):
    common = {
        "ZI": self.XI_mol_in,
        "SkipIndex": self.Is0,
        "DOA": self.DOA,
        "K_time": self.K_time,
        "Instantiation": True,
    }

    if self.TP_BaseOn:
        result = self.flash_TP(
            T=self.T,
            P=self.P_in,
            VF0=self.GasRat0,
            K0=self.K0,
            **common
        )
    elif self.Te_BaseOn:
        result = self.flash_TVF(
            T=self.T,
            VF=self.GasRat,
            P0=self.P0,
            K0=self.K0,
            **common
        )
    elif self.Pe_BaseOn:
        result = self.flash_PVF(
            P=self.P_in,
            VF=self.GasRat,
            T0=self.T0,
            K0=self.K0,
            **common
        )
    elif self.DP_BaseOn:
        if self.F_mol == 0.0:
            raise ValueError("pressure-duty flash requires nonzero outlet flow")
        try:
            inlet_enthalpy_flow = float(self.Fin.FH)
        except (TypeError, ValueError):
            raise ValueError("pressure-duty flash requires inlet enthalpy flow")
        if not np.isfinite(inlet_enthalpy_flow):
            raise ValueError("pressure-duty flash requires inlet enthalpy flow")
        result = self.flash_DP(
            FHin=inlet_enthalpy_flow,
            F_mol=self.F_mol,
            target_duty=self.Duty,
            P=self.P_in,
            T0=self.T0,
            VF0=self.GasRat0,
            K0=self.K0,
            **common
        )
    elif self.DT_BaseOn:
        if self.F_mol == 0.0:
            raise ValueError("temperature-duty flash requires nonzero outlet flow")
        try:
            inlet_enthalpy_flow = float(self.Fin.FH)
        except (TypeError, ValueError):
            raise ValueError("temperature-duty flash requires inlet enthalpy flow")
        if not np.isfinite(inlet_enthalpy_flow):
            raise ValueError("temperature-duty flash requires inlet enthalpy flow")
        result = self.flash_DT(
            FHin=inlet_enthalpy_flow,
            F_mol=self.F_mol,
            T=self.T,
            target_duty=self.Duty,
            P0=self.P0,
            VF0=self.GasRat0,
            K0=self.K0,
            **common
        )
    else:
        raise ValueError("unsupported flash specification")

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

    # Publish state only after the complete result passes validation.
    new_state = {
        "T": float(values[0]),
        "P_in": float(values[1]),
        "GasRat": float(values[2]),
        "XI_mol_in": vectors[0],
        "LXI_mol": vectors[1],
        "VXI_mol": vectors[2],
        "K": vectors[3],
    }

    self.T = new_state["T"]
    self.P_in = new_state["P_in"]
    self.GasRat = new_state["GasRat"]
    self.XI_mol_in = new_state["XI_mol_in"]
    self.LXI_mol = new_state["LXI_mol"]
    self.VXI_mol = new_state["VXI_mol"]
    self.K = new_state["K"]
    return result
```

保留准备组成时成对生成的 `Is0/Not0`。结果中的 `SkipIndex` 用来验证坐标没有变化，
不能只替换 `Is0` 而继续使用旧 `Not0`。不要使用历史 `flashdp`/`flashdt` 名称决定
物理规格。

`Flow.flash_init()` 可能按现有字段可用性进行历史内部派发；该行为只属于 Flow 自身，
新业务规格单元仍按 `*_BaseOn` 分派。

后续能量、物性、utility、结果构建和输出提交都可能失败。`Run()` 必须在调用前保存本次
会修改的全部实例字段和输出 Flow 字段，并在异常路径恢复；或让局部状态贯穿计算并在全部
成功后一次提交。仅延迟 Flow 写入不能保护同样可被外部读取的单元实例状态。

## 相边界与能量

```python
try:
    inlet_enthalpy_flow = float(self.Fin.FH)
except (TypeError, ValueError):
    raise ValueError("energy calculation requires inlet enthalpy flow")
if not np.isfinite(inlet_enthalpy_flow):
    raise ValueError("energy calculation requires inlet enthalpy flow")

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
self.RDuty = self.FH - inlet_enthalpy_flow
```

`get_H_LV_JB` 内部根据 `GasRat` 只调用存在相的焓属性，在 `VF=0/1` 时将不存在相焓
保留为零；业务代码应直接使用该 helper，不自行调用不存在相物性。

若该单元的 `Duty` 是指定值、`RDuty` 是实际值，分别保留，不要无条件互相覆盖。
`get_F_LV_JB` 返回气相流量在前，后续焓流 helper 参数是液相流量在前，因此使用关键字。

边界规则：

- `GasRat <= 0`：`FV_mol=0`，不计算或写入有效气相物性。
- `GasRat >= 1`：`FL_mol=0`，不计算或写入有效液相物性。
- 不存在相的组成不得作为有效流股组成向下游传播。

## 输出 Flow 提交

所有主计算成功后才写端口。输出对象可能被调度器复用，因此每次运行必须同时更新存在相
并清空不存在相，不能保留上一轮状态。以下 `FVout`/`FLout` 为语义名；目标模块若使用
`FDout`/`FWout`，必须先确认哪一个是气相或液相：

```python
if self.FVout is not None:
    vapor_xi = (
        Comp_restore(self.VXI_mol, self.Is0, self.Not0)
        if self.GasRat > 0.0
        else np.zeros(len(self.Fin.XI_mol), dtype=float)
    )
    self.FVout.F_mol = self.FV_mol
    self.FVout.XI_mol = vapor_xi
    self.FVout.FXI_mol = self.FVout.F_mol * self.FVout.XI_mol
    self.FVout.T = self.T
    self.FVout.P_in = self.P_in
    self.FVout.GasRat = 1.0
    self.FVout.FH = self.FHV

if self.FLout is not None:
    liquid_xi = (
        Comp_restore(self.LXI_mol, self.Is0, self.Not0)
        if self.GasRat < 1.0
        else np.zeros(len(self.Fin.XI_mol), dtype=float)
    )
    self.FLout.F_mol = self.FL_mol
    self.FLout.XI_mol = liquid_xi
    self.FLout.FXI_mol = self.FLout.F_mol * self.FLout.XI_mol
    self.FLout.T = self.T
    self.FLout.P_in = self.P_in
    self.FLout.GasRat = 0.0
    self.FLout.FH = self.FHL
```

若 Flow 的 `FXI_mol`、`FH` 是只读派生状态或必须由其自身 `Run()` 生成，则不要直接
赋值，改用该 Flow 已有的状态计算入口。`P_out` 和其他端口字段按目标族契约补齐。

只有一个混合出口的加热/冷却单元应提交总体状态，而不是套用分相端口：

```python
self.Fout.F_mol = self.F_mol
self.Fout.XI_mol = Comp_restore(self.XI_mol_in, self.Is0, self.Not0)
self.Fout.FXI_mol = self.Fout.F_mol * self.Fout.XI_mol
self.Fout.T = self.T
self.Fout.P_in = self.P_in
self.Fout.GasRat = self.GasRat
self.Fout.FH = self.FH
```

不要仅返回 result 字典而遗漏 Flow mutation。

## 公用工程

只有目标基类已证实提供 `Public_F_P` 时才调用：

```python
if self.Utility:
    (
        self.FU_mass,
        self.electricity,
        self.Price_U,
        self.CO2_emissions,
    ) = self.Public_F_P(
        Utility=self.Utility,
        Duty=self.RDuty,
        T=self.T,
    )
```

公用工程是单元配置，不是 Flow 端口。公用工程数据通常来自完整 `Data` 上下文；不在
业务单元中硬编码介质物性或价格。

## feedback 与异常

常见反馈形态是：

```python
self.feedback("warn", "消息", 30000)
self.feedback("error", "消息", 40000)
```

也可能使用 `label/msg/code` 关键字，跟随目标模块。只捕获项目已知的输入、数据或收敛
异常；反馈信息应包含业务规格和可定位上下文。失败后：

1. 清除失效暖启动。
2. 不写输出 Flow。
3. 不用 `nan_to_num` 制造状态。
4. 返回目标模块约定的失败元组，通常为 `(False, {})`。

## 结果字典

遵循平台和目标模块已有输出结构，通常返回 `(True, result)`，属性项形如：

```python
result = {
    "摘要": {
        "出口温度": {"value": self.T, "unitType": "Temperature"},
        "出口压力": {"value": self.P_in, "unitType": "Pressure"},
        "实际热负荷": {"value": self.RDuty, "unitType": "Heat flow"},
    }
}
return True, result
```

中文键和 `unitType` 必须从目标模块族确认，不能从 `phy_prop` 属性代码推导。完整输出
同时包括平台 result、实例状态和下游 Flow 三个独立通道。

## Run 组合模板

下面只表示控制流，字段名和错误码必须按目标模块替换：

```python
def Run(self):
    valid, failure = self.validate_inputs()
    if not valid:
        return failure

    # These helpers must copy every operation/output field changed below,
    # including Is0/Not0, flow, phase, energy, property, and utility fields.
    old_state = self.snapshot_calculation_state()
    old_outputs = self.snapshot_output_flows()

    try:
        self.prepare_composition()
        self.prepare_business_inputs()
        self.prepare_flash_specification_values()
        self.run_flash_specification()
        self.calculate_phase_flow_and_energy()
        self.calculate_optional_properties()
        self.calculate_optional_utility()
        result = self.build_result()
        self.commit_output_flows()
    except (ValueError, RuntimeError) as exc:
        self.restore_calculation_state(old_state)
        self.restore_output_flows(old_outputs)
        self.clear_flash_warm_start()
        self.feedback("error", "单元计算失败: {}".format(exc), 40000)
        return False, {}

    return True, result
```

不要照抄宽泛异常类型；若项目定义了具体数据或收敛异常，应替换为这些类型。不要用
`except Exception` 静默回退到有效相态。快照必须复制可变数组，不能只保存其引用；
恢复输出 Flow 时保持原 Flow 对象身份，只恢复字段，不用深拷贝对象替换端口。

## 完成检查

- 基类、构造参数和端口语义来自目标模块族证据。
- `Input_type1/2` 与 `*_BaseOn` 分派一致。
- 完整组成只在端口使用，闪蒸/物性使用活跃组成加全局 `SkipIndex`。
- 闪蒸结果完整回写，并验证 `SkipIndex` 与保留的 `Is0/Not0` 坐标一致。
- `VF=0/1`、零流量和不存在相得到处理。
- 相流量、焓流参数顺序正确且使用关键字。
- 先完成计算，后提交所有输出端口。
- 失败路径有 feedback，不污染端口，不保留坏暖启动。
- result、实例字段和 Flow 三个输出通道均完成。
- 未臆造 `DutyIn`、MRO、公用工程 API、展示键或错误码。
