# Flash 热负荷与能量公开接口

本文件是 `flash_DP`、`flash_DT`、相流量、相焓、焓流和净热负荷业务接口的唯一事实源。
接口单位和字段含义以
[operation 变量表](../../cslab-operation-unit-skeleton/references/operation-variables.md)
为准。

## 热负荷闪蒸接口

| 方法 | 必需业务输入 | 常用初值/控制 | `Instantiation=False` 返回 |
|---|---|---|---|
| `flash_DP` | `FHin, F_mol, target_duty, P, ZI` | `T0, K0, VF0, 泡露点初值, SkipIndex, DOA, abs_DOA, K_time` | `T, P, VF, LXI_mol, VXI_mol, K` |
| `flash_DT` | `FHin, F_mol, T, target_duty, ZI` | `P0, K0, VF0, 泡露点初值, SkipIndex, DOA, abs_DOA, K_time` | `T, P, VF, LXI_mol, VXI_mol, K` |

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

温度加热负荷反求压力时改用 `flash_DT`，传 `T` 和可选 `P0`。`F_mol` 必须是出口
总摩尔流量且不能为零；`target_duty` 是相对 `FHin` 的净热负荷。求解后按
[状态契约](flash-state-contract.md)校验并完整回写，不能只写回求解的 `T` 或 `P`。

`flash_DT` 在 duty 超出给定温度下的可达区间时可能返回诊断字符串。该返回是受控失败，
不得继续访问 `.T` 或写入出口。

## 相流量、焓和焓流接口

| 方法 | 参数 | 返回 |
|---|---|---|
| `get_F_LV_JB` | `F_mol, VF` | `FV_mol, FL_mol` |
| `get_H_LV_JB` | `T, P, VF, LXI_mol, VXI_mol, SkipIndex` | `H_mol, HL_mol, HV_mol` |
| `get_H_F_LV_JB` | `F_mol, FL_mol, FV_mol, H_mol, HL_mol, HV_mol` | `FH, FHL, FHV` |
| `get_duty_by_flash` | 目标模块已有的入口焓流和闪蒸状态 | 相对入口的净热负荷 |

闪蒸成功并完成状态校验后按下列顺序调用：

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

`get_H_LV_JB` 根据 `VF` 只计算存在相，不存在相焓保持为零。必须传闪蒸返回的同坐标
相组成并调用一次，不在业务层重写相焓分支。

`get_F_LV_JB` 返回气相在前 `(FV_mol, FL_mol)`，而 `get_H_F_LV_JB` 的参数是液相
流量在前；调用后者必须使用关键字。已知入口焓流并完成出口闪蒸时，使用
`get_duty_by_flash` 计算净热负荷，不手工重复相焓选择。
