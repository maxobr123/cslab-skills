# FlashTank 反应、出口与字段发布

仅当已确认的 FlashTank 模板包含反应、`FDout/FWout`、`DutyIn` 或专用实例输出时读取。
变量含义和单位以
[`operation-variables.md`](../../cslab-operation-unit-skeleton/references/operation-variables.md)
为唯一事实源。

## 反应调用边界

只有目标 MRO 确认提供 `ReactionBase` 且 `RList` 非空时执行反应。历史 FlashTank 契约采用
入口流股口径：组分摩尔流量和相体积流量来自 `FFin`，调用时 `VF=0`。仅在目标族证实仍
使用该口径时采用以下范式：

```python
def getReaction(self):
    self.F_vol = self.FFin.F_vol
    if self.RList:
        (
            self.FXI_mol_out,
            self.FL_mol,
            self.LXI_mol,
            reaction_state,
            self.FV_mol,
            self.VXI_mol,
        ) = self.Reaction_Base(
            comp_list=self.Data.CAS,
            FXI_mol_L=self.FFin.FLXI_mol,
            FXI_mol_V=self.FFin.FVXI_mol,
            F_vol_L=self.FFin.FL_vol,
            F_vol_V=self.FFin.FV_vol,
            RP=self.P_in,
            RT=self.T,
            VF=0,
        )
```

返回值中未被消费者读取的局部量使用有含义的局部名，不为了历史字段外观创建实例属性。
该历史口径只更新经确认的反应相关输出，不擅自回改 Flash 得到的总流量、总体组成和 VF。
如果当前反应模型定义了不同物料边界，以模板、方程和开发者确认的技术方案为准。

## 分相出口提交

FlashTank 的具体端口含义必须由模板确认。已验证 `FDout` 为气相、`FWout` 为液相时，所有
计算成功且相组成恢复为完整坐标后，可按以下范式提交：

```python
self.FDout.F_mol = self.FV_mol
self.FDout.P_in = self.P_in
self.FDout.T = self.T
self.FDout.XI_mol = self.VXI_mol
self.FDout.GasRat = 1.0

self.FWout.F_mol = self.FL_mol
self.FWout.P_in = self.PW_out
self.FWout.T = self.T
self.FWout.XI_mol = self.LXI_mol
self.FWout.GasRat = 0.0
```

这里假定 `VXI_mol/LXI_mol` 已经 `Comp_restore`。如果实例仍保存活跃坐标，先生成完整坐标
局部变量再发布，不能改变同名字段的坐标语义。`PW_out` 只在模板和容器计算确实提供罐底
压力时使用，否则按目标出口压力契约处理。

输出 Flow 被复用时，本轮不存在相也必须将流量、组成和派生状态清空，不能保留上轮相态。
若 Flow 要求由自身公开入口计算 `FXI_mol/FH` 等派生字段，调用该入口而不是手工赋值。

## 能量流反向发布

只有模板存在 `DutyIn` 且下游消费者需要换热端温度时才反向写入：

```python
if self.DutyIn is not None:
    self.DutyIn.T0 = self.T
    self.DutyIn.T1 = self.T + 2.0 if self.duty > 0.0 else self.T - 2.0
```

`2.0 K` 是历史 FlashTank 契约值，不是通用换热模型。当前模板、能量流算法或技术方案没有
确认该约定时，不得照抄；应由开发者确认真实端温差模型。

## 实例字段与结果发布

按消费者矩阵逐项发布：

| 通道 | 发布条件 | 发布内容 |
|---|---|---|
| 实例属性 | 模板输出需要前端、落库或模块引用 | 严格同名、正确类型/坐标的本轮值 |
| `FDout/FWout` | 下游节点已连接并读取 | 相流量、完整组成、T、P、相态及 Flow 契约要求的派生字段 |
| `DutyIn` | 能量流消费者已确认 | 目标契约要求的 Duty 或端温字段 |
| 稳态 `result` | 控制器确认消费入口返回 | 同族已验证中文键、`value` 和 `unitType` |

没有消费者的通道不构造占位数据；不能因为不需要 `result` 就遗漏实例属性或 Flow。模板中
存在的输出属性若被框架按属性 ID 落库，即使 Python 内部不读取，也属于真实消费者，必须
初始化并在成功路径更新。

## 提交检查

- 反应能力、口径、输入字段和返回值来自当前族证据。
- 写 Flow 前已恢复完整项目组分坐标，并处理 VF 单相边界。
- `PW_out`、`DutyIn` 端温差和结果展示键均有模板或消费者证据。
- 失败时没有部分写入实例属性、输出 Flow 或能量流。
- 未生成无消费者的反应字段、容器字段、结果字典或辅助方法。
