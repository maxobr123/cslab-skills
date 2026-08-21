# `phy_prop` 多工况矩阵调用契约

数组输入仍调用唯一公开入口 `phy_prop`，由其自动进入矩阵路径。不要直接调用
`phy_propArray`、内部属性类的 `CalculateArray`，也不要为批量功能写逐工况标量循环。

## 调用示例

```python
def calculate_vapor_enthalpy_cases(self, t_cases, p_cases, y_cases):
    t_arr = np.asarray(t_cases, dtype=float)
    p_arr = np.asarray(p_cases, dtype=float)
    y_arr = np.asarray(y_cases, dtype=float)

    if t_arr.ndim != 1 or p_arr.shape != t_arr.shape:
        raise ValueError("T and P must be paired one-dimensional cases")
    if y_arr.ndim != 2 or y_arr.shape[0] != t_arr.shape[0]:
        raise ValueError("XI rows must match the number of cases")

    return self.phy_prop(
        Property="H_V_MIX",
        T=t_arr,
        P=p_arr,
        XI_mol=y_arr,
        SkipIndex=self.Is0,
    )
```

## 输入语义

1. `T.shape == P.shape == (case_count,)`；同一下标是一组配对工况，不生成笛卡尔积。
2. 混合组成 `XI.shape == (case_count, active_component_count)`。
3. 框架不自动广播标量、不重复组成、不归一化数组、不转换完整坐标到局部坐标。
4. 固定组成必须由调用方显式 `repeat`/`tile` 成二维矩阵。
5. `XI` 与 `XI_mol` 二选一，组成列必须与 `SkipIndex` 定义的活跃组分一致。
6. 闪蒸 `flash_*` 是单工况迭代接口，不能接收这些矩阵。

## 返回 shape

- 纯组分或逐组分属性通常返回 `(case_count, active_component_count)`。
- 混合物标量属性通常返回 `(case_count,)`。
- `GAMMAS`、`PHI_L_MIX`、`PHI_V_MIX` 等混合向量返回
  `(case_count, active_component_count)`。
- 每个属性的最终返回形态以[属性目录](property-catalog.md)为准。

`Henry`、`DC`、`CP_INF`、`S_INF` 不作为标准矩阵业务接口使用。
