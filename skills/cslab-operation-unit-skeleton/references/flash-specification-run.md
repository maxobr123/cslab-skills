# 稳态单元规格执行与状态事务

仅当 operation 单元需要组成过滤、Flash 规格分派、相能量计算、暖启动或失败回滚时读取。
变量含义、单位和坐标统一查阅
[`operation-variables.md`](operation-variables.md)，本文不重复变量表。Flash 方法的准确签名和
返回契约以 `cslab-operation-flash` 为准。

## 目录

- [从零开发的最小端口范式](#从零开发的最小端口范式)
- [输入与组成准备](#输入与组成准备)
- [规格值准备](#规格值准备)
- [规格分派与结果校验](#规格分派与结果校验)
- [相边界与能量](#相边界与能量)
- [状态事务与控制流](#状态事务与控制流)

## 从零开发的最小端口范式

需求、模板和既有同族模块都未规定端口时，才可采用以下默认语义：

| 新单元类型 | 构造器注入 | 状态/规格字段 | 输出语义 |
|---|---|---|---|
| TP 气液分离器 | `Fin, FVout, FLout, Data, Method_bag` | `T, P_in` | `FVout` 纯气相，`FLout` 纯液相 |
| 压力加 duty 单出口单元 | `Fin, Fout, Data, Method_bag` | `P_in, Duty` | `Fout` 为总体闪蒸后流股 |

这些名称只是从零开发的默认值。明确契约优先；两个范式均通过继承 Flash-capable 基类取得
算法，并保存外部注入的 Flow，不在 `Run()` 内重建端口。

## 输入与组成准备

校验实际规格需要的端口、有限标量、流量、组成和入口焓流。失败上报、错误码和入口返回
严格使用 `cslab-module-contract` 及目标控制器契约，本文不重复定义；失败后不继续计算或
写输出 Flow。

零流量按单元物理意义处理：允许旁路时显式复制安全字段；不允许时受控失败。禁止把零流量
送入 `flash_DP` 或 `flash_DT`。

```python
def prepare_composition(self):
    try:
        full_xi = np.asarray(self.Fin.XI_mol, dtype=float)
    except (TypeError, ValueError):
        raise ValueError("入口组成无法转换为数值向量")
    if full_xi.ndim != 1 or full_xi.size != self.Data.Length:
        raise ValueError("入口组成长度或维度无效")
    if not np.all(np.isfinite(full_xi)):
        raise ValueError("入口组成包含非有限值")
    if np.any(full_xi < 0.0) or full_xi.sum() <= 0.0:
        raise ValueError("入口组成必须非负且总和大于零")

    xi_sum = full_xi.sum()
    if not np.isclose(xi_sum, 1.0, rtol=1e-6, atol=1e-8):
        raise ValueError("入口组成未归一化")
    full_xi = full_xi / xi_sum
    self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(full_xi)
```

无反应、无侧线时，在规格分派前显式令出口总摩尔流量等于入口值。热负荷规格要求入口
`Fin.FH` 已由 Flow 的完整状态工作流产生且为有限值；没有已验证入口时受控失败，不在业务
层手工拼纯物性猜测焓流。

## 规格值准备

只转换当前分派需要的字段。布尔值不是合法实数；温度和压力必须为正，汽化率在 `[0, 1]`。
目标族使用小写 `duty` 时整体替换字段名，不同时维护两个可能分叉的值。

```python
def require_finite_scalar(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("{} 必须是实数".format(name))
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError("{} 必须是实数".format(name))
    if not np.isfinite(result):
        raise ValueError("{} 必须是有限值".format(name))
    return result


def prepare_flash_specification_values(self):
    if self.TP_BaseOn or self.Te_BaseOn or self.DT_BaseOn:
        self.T = require_finite_scalar(self.T, "T")
        if self.T <= 0.0:
            raise ValueError("T 必须大于 0 K")

    if self.TP_BaseOn or self.Pe_BaseOn or self.DP_BaseOn:
        self.P_in = require_finite_scalar(self.P_in, "P_in")
        if self.P_in <= 0.0:
            raise ValueError("P_in 必须大于 0 Pa")

    if self.Te_BaseOn or self.Pe_BaseOn:
        self.GasRat = require_finite_scalar(self.GasRat, "GasRat")
        if not 0.0 <= self.GasRat <= 1.0:
            raise ValueError("GasRat 必须位于 0 到 1")

    if self.DP_BaseOn or self.DT_BaseOn:
        self.Duty = require_finite_scalar(self.Duty, "Duty")
```

`T0/P0/VF0/K0` 仅是可选暖启动。复用前检查有限性、范围、方法包和组分坐标；任一不一致
就清空相应初值，不能让坏初值进入求解器。

## 规格分派与结果校验

`*_BaseOn` 由已经确认的输入规格组合产生，不根据状态字段是否恰好非空自行推断。
`Flow.flash_init()` 的历史内部派发只属于 Flow；新业务规格单元仍按已验证分派标志调用。

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
            T=self.T, P=self.P_in, VF0=self.GasRat0, K0=self.K0, **common
        )
    elif self.Te_BaseOn:
        result = self.flash_TVF(
            T=self.T, VF=self.GasRat, P0=self.P0, K0=self.K0, **common
        )
    elif self.Pe_BaseOn:
        result = self.flash_PVF(
            P=self.P_in, VF=self.GasRat, T0=self.T0, K0=self.K0, **common
        )
    elif self.DP_BaseOn:
        if self.F_mol == 0.0:
            raise ValueError("压力-热负荷闪蒸要求非零出口流量")
        inlet_fh = require_finite_scalar(self.Fin.FH, "Fin.FH")
        result = self.flash_DP(
            FHin=inlet_fh,
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
            raise ValueError("温度-热负荷闪蒸要求非零出口流量")
        inlet_fh = require_finite_scalar(self.Fin.FH, "Fin.FH")
        result = self.flash_DT(
            FHin=inlet_fh,
            F_mol=self.F_mol,
            T=self.T,
            target_duty=self.Duty,
            P0=self.P0,
            VF0=self.GasRat0,
            K0=self.K0,
            **common
        )
    else:
        raise ValueError("不支持的闪蒸规格组合")

    required = ("T", "P", "VF", "ZI", "LXI_mol", "VXI_mol", "K", "SkipIndex")
    if isinstance(result, str) or not all(hasattr(result, name) for name in required):
        raise RuntimeError(str(result))
    return result
```

完整结果校验至少包含：

1. `T/P/VF` 是有限实数，且满足正温度、正压力和汽化率范围。
2. `ZI/LXI_mol/VXI_mol/K` 都是一维活跃坐标向量，长度和有限性正确。
3. 进料组成归一化；存在相的相组成非负且归一化；K 值非负。
4. 返回 `SkipIndex` 与本轮 `Is0` 完全一致，不能只替换 `Is0` 而继续使用旧 `Not0`。

校验完整结果后再同时更新 `T/P_in/GasRat/XI_mol_in/LXI_mol/VXI_mol/K`。不要使用历史
`flashdp`/`flashdt` 名称判断物理规格。

## 相边界与能量

直接复用已验证的相流量、相焓和焓流 helper，不自行调用不存在相的物性：

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
self.RDuty = self.FH - float(self.Fin.FH)
```

`get_F_LV_JB` 返回气相流量在前，而焓流 helper 的参数是液相流量在前，因此必须使用
关键字。指定热负荷与实际净热负荷分别保存，不无条件互相覆盖。

- `GasRat <= 0`：气相流量为零，不发布有效气相物性。
- `GasRat >= 1`：液相流量为零，不发布有效液相物性。
- 不存在相的组成不能作为有效流股组成传播。

## 状态事务与控制流

能量、物性、公用工程、结果构建和 Flow 提交都可能失败。让局部待提交状态贯穿计算，或在
调用前保存本轮会修改的全部实例字段及输出 Flow 字段；异常时完整恢复。仅延迟 Flow 写入，
不能保护可被外部读取的实例状态。

```python
def Run(self):
    valid, failure = self.validate_inputs()
    if not valid:
        return failure

    # 快照必须覆盖随后会修改的实例字段、可变数组和输出 Flow 字段。
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
        result = self.build_consumed_result()
        self.commit_output_flows()
    except (ValueError, RuntimeError):
        self.restore_calculation_state(old_state)
        self.restore_output_flows(old_outputs)
        self.clear_flash_warm_start()
        # 按 module-contract 和目标控制器契约完成失败上报及入口退出。
        raise

    return True, result
```

异常类型必须替换为目标族已验证契约。示例中的再次抛出只表示“不要吞掉失败”，实际由
`cslab-module-contract` 和控制器约定决定是反馈后返回还是传播明确异常。不要用宽泛
`except Exception` 静默制造有效相态，也不要用 `nan_to_num` 隐藏算法失败。恢复 Flow 字段
时保留原对象身份，不用深拷贝对象替换外部注入端口。
