# `phy_prop` 相存在性与能量规则

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
`VF=0` 时不调用气相属性，`VF=1` 时不调用液相属性。输入组成必须是该相的活跃局部
组成，并携带同一组 `SkipIndex`。

## 能量计算层级

单独研究某一相或塔板属性时，可以直接调用 `H_L_MIX` 或 `H_V_MIX`。完整流程闪蒸后的
相焓、总焓、焓流和 duty 必须使用 `cslab-operation-flash` 中的公共组合方法：

- `get_H_LV_JB(...)`：按相存在性计算总/液/气相摩尔焓。
- `get_F_LV_JB(...)`：由总摩尔流量和汽化率计算相流量。
- `get_H_F_LV_JB(...)`：计算总/液/气相焓流。
- `get_duty_by_flash(...)`：计算相对入口焓流的净热负荷。

具体参数、返回顺序和调用代码只以
[Flash 热负荷与能量接口](../../cslab-operation-flash/references/flash-duty-energy-api.md)
为准，不在本文件复制。不要在业务层重写两相焓选择，也不要因已有 `H_L`/`H_V` 就
假定简单加权等价于 `H_L_MIX`/`H_V_MIX`。
