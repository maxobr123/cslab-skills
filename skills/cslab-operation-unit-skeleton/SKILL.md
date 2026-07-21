---
name: cslab-operation-unit-skeleton
description: Use when developing a CSLAB domain/operation Run() business unit with Flow ports, Flash condition dispatch, heat duty, feedback, or utility accounting.
---

# CSLAB 业务单元骨架

本 Skill 用于编排业务单元 `Run()`，覆盖流股读写、规格分派、热负荷、反馈、公用工程
与受控结果输出。闪蒸参数查 `domain/operation/Flash.pyi`，物性选择查
`cslab-operation-phy-prop`，闪蒸算法和模板查 `cslab-operation-flash`。

## API 查询优先级

1. 先读 `domain/operation/Flash.pyi`，确认 `Flash` 公共方法、关键字参数、
   `FlashResults` 字段与 `Instantiation` 返回形态。
2. 再读本单元相邻的同类模块，确认本模块的构造参数、输入输出端口和错误码号段。
3. 不依赖 `.pyd` 的未声明成员，不反编译、探测或 monkey patch 编译模块。
4. `Utility_U`、`Vessel`、`ReactionBase` 在当前环境可能只有 `.pyd`。未取得经过验证的
   `.pyi` 前，不推测它们的 MRO、构造参数或公共方法。

## 基类选择

| 业务目标 | 首选基类/模式 |
|---|---|
| 完整流股状态、相态和物性 | `Flow(Flash)` |
| 输入适配 | `Feed(Flash)`，将字段写入 `Fout: Flow` |
| 仅需常规闪蒸组合 | `Flash` 子类 |
| 反应器并需公用工程核算 | 参考相邻 `Utility_U` 单元；先确认可用公共 Stub |

不要假设所有流程单元都继承同一条链。尤其不要因类名推测 `Utility_U` 与
`Vessel`、`ReactionBase` 的继承关系。

## Flow 端口契约

输入流股最常用字段：

| 字段 | 含义 | 单位 |
|---|---|---|
| `T` | 温度 | K |
| `P_in` | 流股计算压力 | Pa |
| `P_out` | 出口/下游压力约定 | Pa |
| `F_mol` | 总摩尔流量 | kmol/s |
| `XI_mol` | 全组分摩尔组成 | 无量纲 |
| `FXI_mol` | 全组分组分摩尔流量 | kmol/s |
| `FH` | 总焓流 | J/s（W） |
| `GasRat` | 气化率 | 无量纲 |

闪蒸后的活跃坐标字段为 `XI_mol_in`、`LXI_mol`、`VXI_mol`。需要对外输出全组分
向量时，用 `Comp_restore(values, Is0, Not0)` 恢复，不要将局部向量直接写给下游 Flow。

气液分离出口的最小回写形式：

```python
if self.GasRat > 0.0 and self.FDout is not None:
    self.FDout.F_mol = self.FV_mol
    self.FDout.XI_mol = Comp_restore(self.VXI_mol, self.Is0, self.Not0)
    self.FDout.T = self.T
    self.FDout.P_in = self.P_in

if self.GasRat < 1.0 and self.FWout is not None:
    self.FWout.F_mol = self.FL_mol
    self.FWout.XI_mol = Comp_restore(self.LXI_mol, self.Is0, self.Not0)
    self.FWout.T = self.T
    self.FWout.P_in = self.P_in
```

端口语义以目标模块构造参数为准：现有反应器常将 `FDout` 用作气相出口、`FWout`
用作液相出口，但新模块不能仅根据变量名猜测。

## Run 分派骨架

当单元使用 `Input_type1` / `Input_type2` 时，按 `Flash.pyi` 声明的只读规格标志分派：

```python
def run_flash_specification(self):
    if self.TP_BaseOn:
        result = self.flash_TP(
            T=self.T, P=self.P_in, ZI=self.XI_mol_in,
            SkipIndex=self.Is0, VF0=self.GasRat0, K0=self.K0,
            DOA=self.DOA, K_time=self.K_time, Instantiation=True,
        )
    elif self.Te_BaseOn:
        result = self.flash_TVF(
            T=self.T, VF=self.GasRat, ZI=self.XI_mol_in,
            P0=self.P0, K0=self.K0, SkipIndex=self.Is0,
            DOA=self.DOA, K_time=self.K_time, Instantiation=True,
        )
    elif self.Pe_BaseOn:
        result = self.flash_PVF(
            P=self.P_in, VF=self.GasRat, ZI=self.XI_mol_in,
            T0=self.T0, K0=self.K0, SkipIndex=self.Is0,
            DOA=self.DOA, K_time=self.K_time, Instantiation=True,
        )
    elif self.DP_BaseOn:
        result = self.flash_DP(
            FHin=self.Fin.FH, F_mol=self.Fin.F_mol,
            target_duty=self.Duty, P=self.P_in, ZI=self.XI_mol_in,
            T0=self.T0, VF0=self.GasRat0, K0=self.K0,
            SkipIndex=self.Is0, DOA=self.DOA, K_time=self.K_time,
            Instantiation=True,
        )
    elif self.DT_BaseOn:
        result = self.flash_DT(
            FHin=self.Fin.FH, F_mol=self.Fin.F_mol,
            T=self.T, target_duty=self.Duty, ZI=self.XI_mol_in,
            P0=self.P0, VF0=self.GasRat0, K0=self.K0,
            SkipIndex=self.Is0, DOA=self.DOA, K_time=self.K_time,
            Instantiation=True,
        )
    else:
        self.feedback("error", "未识别的闪蒸规格", 40000)
        return None

    self.T = result.T
    self.P_in = result.P
    self.GasRat = result.VF
    self.XI_mol_in = result.ZI
    self.LXI_mol = result.LXI_mol
    self.VXI_mol = result.VXI_mol
    self.K = result.K
    return result
```

`40000` 是通用 error 代码示例，必须替换为相邻同类模块实际使用的错误码号段。`*_BaseOn`
根据 `Input_type1/Input_type2` 的中文规格组合判断，不根据字段是否为 `None` 自动置位。

## 能量与公用工程

入口能量使用 `Fin.FH`，不要臆造 `DutyIn` 字段。闪蒸后按公共辅助方法计算：

```python
self.H_mol, self.HL_mol, self.HV_mol = self.get_H_LV_JB(
    T=self.T, P=self.P_in, VF=self.GasRat,
    LXI_mol=self.LXI_mol, VXI_mol=self.VXI_mol, SkipIndex=self.Is0,
)
self.FV_mol, self.FL_mol = self.get_F_LV_JB(self.F_mol, self.GasRat)
self.FH, self.FHL, self.FHV = self.get_H_F_LV_JB(
    self.F_mol, self.FL_mol, self.FV_mol,
    self.H_mol, self.HL_mol, self.HV_mol,
)
self.RDuty = self.FH - self.Fin.FH
```

公用工程是可选单元配置，而不是 `Flow` 端口。已有 `Utility_U` 单元采用：

```python
if self.Utility:
    self.FU_mass, self.electricity, self.Price_U, self.CO2_emissions = self.Public_F_P(
        Utility=self.Utility,
        Duty=self.RDuty,
        T=self.T,
    )
```

仅在目标 `Utility_U` 的公共 Stub 或已验证 API 已声明 `Public_F_P` 时使用此模板。

## feedback 与受控失败

运行装配器会将回调注入单元实例。按以下协议调用：

```python
self.feedback("warn", "消息", 30000)
self.feedback("error", "消息", 40000)
```

`3xxxx` 是 warning，`4xxxx` 是 error。不要复用其他模块含义不一致的历史代码；优先
沿用目标模块相邻单元的号段。反馈后按邻近模块的既有形态返回，例如 `(False, {})` 或
`(True, self.result_fail)`，不要吞异常后继续写入无效流股。

## 禁止事项

1. 不将活跃组分局部相组成直接写入全组分 Flow 端口。
2. 不把 `flash_*` 的失败状态用 `np.nan_to_num` 伪造成有效 `T/P/VF/K/x/y`。
3. 不根据 `T/P/VF/Duty` 是否为空猜测 `*_BaseOn`，也不沿用历史 `flashdp/flashdt` 的反向命名。
4. 不假定存在 `DutyIn`、`Vessel` 或 `ReactionBase` 的未验证公共字段或方法。
5. 不绕过 `feedback`、流量/组成校验或既有受控失败返回。
