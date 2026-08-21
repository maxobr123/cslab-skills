# Flow 输出、公用工程与消费者发布

仅当稳态 operation 需要回写分相/总体出口、调用公用工程或组织多通道输出时读取。字段
含义与单位统一查阅 [`operation-variables.md`](operation-variables.md)。返回值是否需要构造、
`feedback` 和最小实现以 `cslab-module-contract` 为准。

## 输出提交原则

1. 所有主计算成功后才写端口；输出 Flow 可能被调度器跨轮复用。
2. 每轮同时更新存在相并清空不存在相，不能遗留上一轮的组成、流量或焓流。
3. Flash 活跃组成经 `Comp_restore(values, Is0, Not0)` 恢复后才能写 Flow 完整坐标。
4. `result`、实例模板属性、输出 Flow 和能量流是独立通道，只写真实消费者需要的通道。
5. 端口字段若由 Flow 自身 `Run()` 或只读派生状态维护，调用其公开工作流，不直接赋值。

以下名称是语义示例。目标模板使用 `FDout/FWout` 等名称时，先确认哪个端口对应气相或
液相，不能凭名称猜测。

## 分相出口范式

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

`P_out` 及其他节点字段按目标 Flow 契约补齐。不存在相的零向量只用于清除复用端口旧值，
不得当作有效相组成参与后续物性计算。

## 总体出口范式

只有一个混合出口的加热、冷却或调压单元提交总体状态，不套用分相端口：

```python
self.Fout.F_mol = self.F_mol
self.Fout.XI_mol = Comp_restore(self.XI_mol_in, self.Is0, self.Not0)
self.Fout.FXI_mol = self.Fout.F_mol * self.Fout.XI_mol
self.Fout.T = self.T
self.Fout.P_in = self.P_in
self.Fout.GasRat = self.GasRat
self.Fout.FH = self.FH
```

只返回结果字典而遗漏下游消费者所需的 Flow mutation，不算完成。

## 公用工程范式

只有目标基类已验证提供 `Public_F_P` 且模板配置了公用工程时才调用：

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

公用工程是单元配置，不是 Flow 端口。数据来自完整 `Data` 上下文；业务单元不硬编码介质
物性、价格或碳排因子。`Duty` 参数使用指定值还是实际值，必须按目标 `Public_F_P` 契约确认。

## 消费者驱动结果

平台确认消费稳态入口结果时，遵循目标同族已有中文展示键和 `unitType`：

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

示例键不是全局规范，不能从 `phy_prop` 属性代码推导展示键。控制器不消费入口业务结果时，
不要为了统一外观构造 `result` 或空字典；仍需发布已确认的实例属性和下游端口消费者。

## 发布检查

- 已列出每个输出通道的消费者、字段、坐标和验证方式。
- 存在相与不存在相都被本轮状态覆盖，没有跨轮残值。
- 总体/分相出口、压力边界和焓流口径符合目标单元族。
- 未证实 `Public_F_P`、Utility 配置或展示消费者时，没有构造相关代码。
