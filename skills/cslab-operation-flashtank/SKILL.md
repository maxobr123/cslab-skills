---
name: cslab-operation-flashtank
description: Use only when writing or modifying a FlashTank-family steady-state unit in domain/operation whose template or verified contract uses FFin/FDout/FWout, Flash specification dispatch, vessel fields, reaction support, or utility accounting.
---

# FlashTank 家族专用骨架(operation 族,L3)

本 Skill 只定义 FlashTank（平衡闪蒸罐）及经模板确认与其同契约模块的专用范式。
不得把这里的 MRO、`FFin/FDout/FWout`、`DutyIn`、容器字段或反应字段套到 Heater、
Pump 或其他稳态单元。通用稳态单元先读 `cslab-operation-unit-skeleton`；确认目标属于
FlashTank 家族后再加载本文。必须沿用该家族已验证的变量名与继承方法，不发明同义新名、
不重写基类算法。平台通用契约见 `cslab-module-contract`；闪蒸方法细节见
`cslab-operation-flash`,物性方法见 `cslab-operation-phy-prop`。

## 继承与 __init__ 模式

```python
from domain.operation.Flow import Flow
from domain.operation.Flash import Flash
from domain.operation.Public import Utility_U
from domain.baseClass.ReactionBase import ReactionBase
from domain.baseClass.Vessel import Vessel
from domain.math.mathmethod import Comp_restore, Comp_filter


def feedback_func(*args, **kwargs): pass


class MyTank(Utility_U, Vessel, ReactionBase):
    def __init__(self, FFin: Flow, FDout: Flow, FWout: Flow,
                 Input_type1=None, Input_value1=None,
                 Input_type2=None, Input_value2=None,
                 Method_bag=None, Data=None, mode=None,
                 DT=0.01, DOA=1e-9, K_time=200,
                 Utility=None,
                 Height=None, Diameter=None,
                 **kwargs):
        super().__init__(Data=Data, Method_bag=Method_bag, DT=DT, DOA=DOA, K_time=K_time)
```

1. 形参顺序:流股对象在前(`FFin`/`FDout`/`FWout`,多流股用 `Flow_list`),
   然后输入条件对、`Method_bag`/`Data`、迭代参数、设备参数,末尾 `**kwargs`。
2. 仅当目标 FlashTank 模板或本家族已验证契约包含对应能力时组合基类：闪蒸/物性能力
   来自 Flash 家族，公用工程使用 `Utility_U`，容器使用 `Vessel`，反应使用
   `ReactionBase`。不得据此推断其他 operation 模块的 MRO。
3. 公用工程惯用法:`if Utility: self.Utility = self.Data.PUW[Utility]`。
4. 反应门控:`self.RList`(反应 id 列表)非空才做反应计算。
5. **输出/占位属性必须在 `__init__` 初始化**(0 或零向量):模板中所有
   `is_input=否` 的属性,以及动态占位属性(如 `HHL`、`PW`、`H_dewT`、`H_satT`、
   `V_mol`、`L_mol`、`FY_mol`、`FY_mass`、`LXI_mass`、`VXI_mass`、`VXI_mol`、
   `Q`、`n_num_mol`、`FY_VXI_mol`、`KA_Cont`、`P_A_Ideal` 等,按模板而定)。
   未初始化的属性会导致落库比对与后续访问出错;**落库属性改名 = 字段丢失**。

## 标准变量词汇表

| 变量 | 含义 | 单位 |
|---|---|---|
| `self.T` / `self.T0` | 温度 / 初值 | K |
| `self.P_in` / `self.P0` | 操作(进口)压力 / 初值 | Pa |
| `self.P_out` | 出口压力 | Pa |
| `self.VF` = `self.GasRat` / `self.VF0` | 汽化率 / 初值(业务层用 VF,基类字段是 GasRat,保持同步) | - |
| `self.duty` / `self.duty0` | 热负荷 / 初值 | W |
| `self.F_mol` | 总摩尔流量 | kmol/s |
| `self.FL_mol` / `self.FV_mol` | 液/汽相摩尔流量 | kmol/s |
| `self.XI_mol` / `self.XI0` | 进料摩尔分率(全组分坐标) | - |
| `self.LXI_mol` / `self.VXI_mol` | 液/汽相摩尔分率 | - |
| `self.K` / `self.K0` | 相平衡常数 / 初值 | - |
| `self._Is0` / `self.Not0` | `Comp_filter` 返回的零/非零组分全局索引 | - |
| `self.Flash_core` | 闪蒸返回的 `FlashResults` | - |
| `self.A` | 相平衡非理想修正 | - |
| `self.Data` / `self.comp` | 物性数据对象 / `self.Data.comp` | - |
| `self.DT` / `self.DOA` / `self.K_time` | 步长 / 收敛精度 / 最大迭代 | - |
| `self.mode` | 0 设计 / 1 校核 | - |
| `self.T_init` / `self.P_init` / `self.duty_init` | 输入条件的原始记录(`get_value` 赋值,`P_init` 兼作"压力是否为输入"判据) | - |
| `self.Pressure_drop` | 压降(`FFin.P_out - self.P_in`) | Pa |
| `self.Density_mol` | 液相混合摩尔密度(`phy_prop` 的 `DS_L_MIX` 结果) | kmol/m3 |
| `self.MW_avg` | 液相平均分子量(`sum(Data.MW[Not0] * LXI_mol)`) | kg/kmol |
| `self.DutyIn` | 能量流对象(`.Duty`、`.T0`、`.T1`),未连接为 None | - |

容器类(`Vessel`)另有:`Height` 罐高、`Diameter` 直径、`LHMP`/`LLMP` 高/低液位
测点、`LRAT`/`PRAT`/`TRAT`、`HHL` 液位、`PW_out` 罐底压力(静液柱:
`液相混合摩尔密度 * 平均分子量 * 9.81 * Height * 0.5 + P_in`)。

`Data` 对象字段:`Data.comp`(`[{"cas","alias",...}]`)、`Data.CAS`、`Data.MW`
(支持 `Data.MW[self.Not0]` 索引)、`Data.PUW` 公用工程字典、
`Data.binaryData_all`(键=方法包 id)、`Data.methodBag[Method_bag]` 方法包配置、
`Data.ReactionData`。缺省方法包 id:`list(Data.binaryData_all.keys())[0]`。

## 继承方法词汇表

| 来源 | 方法 | 用途 |
|---|---|---|
| Flash 家族 | `flash_TP` / `flash_TVF` / `flash_PVF` / `flash_TPVF` / `flash_BubT` / `flash_DewT` / `flash_BubP` / `flash_DewP` / `flash_DP` / `flash_DT` / `flash_HP` / `LLE` / `VLLE` | 闪蒸与泡露点,签名见 `cslab-operation-flash` |
| Flash 家族 | `phy_prop` | 标量/矩阵统一物性入口,见 `cslab-operation-phy-prop` |
| Flash 家族 | `get_H_LV_JB` / `get_F_LV_JB` / `get_H_F_LV_JB` / `get_duty_by_flash` | 相焓/相流量/焓流/热负荷组合 |
| `Utility_U` | `Public_F_P(Utility=self.Utility, Duty=self.duty, T=self.T)` → `(FU_mass, electricity, Price_U, CO2_emissions)` | 公用工程耗量/电耗/费用/碳排 |
| `ReactionBase` | `Reaction_Base(comp_list=, FXI_mol_L=, FXI_mol_V=, F_vol_L=, F_vol_V=, RP=, RT=, VF=)` → `(FXI_mol_out, FL_mol, LXI_mol, A, FV_mol, VXI_mol)` | 反应计算,标准调用见下方 `getReaction` |
| `domain.math.mathmethod` | `Comp_filter(XI)` → `(活跃组成, _Is0, Not0)`;`Comp_restore(v, _Is0, Not0)` → 全长数组 | 组分过滤/恢复 |

## 输入条件与 *_BaseOn 分派

输入以 `Input_type1/Input_value1`、`Input_type2/Input_value2` 两对给出,类型
枚举 `"温度" / "压力" / "汽化率" / "热负荷"`。`get_value()` 惯用法:

- `"温度"` → `self.T = self.T_init = value`
- `"压力"` → 值 > 0:`self.P_in = self.P_init = value` 并同步
  `self.FFin.P_out = self.P_in`;值 ≤ 0 表示相对上游的压差:
  `self.P_in = self.P_init = self.FFin.P_out + value`
- `"汽化率"` → `self.VF = self.GasRat = value`
- `"热负荷"` → `self.duty = self.duty_init = value`
- `get_value()` 末尾固定校验:`if not self.P_init: self.feedback("warn",
  "压力不是输入条件")`(无对应码,不带 code)。
- 连接能量流时 `set_duty()` 强制第二条件为热负荷:`self.Input_type2 = "热负荷";
  self.Input_value2 = self.DutyIn.Duty`,为 0 时 warn 码 30602。

基类根据 T/P/VF/duty 哪些已知置位分派标志,`Run()` 按标志走分支,**不要自己
写输入组合判断替代它**:

| 标志 | 已知 | 调用 | 补算 |
|---|---|---|---|
| `self.TP_BaseOn` | T, P | `flash_TP` | `get_duty_by_flash` 求 duty |
| `self.Te_BaseOn` | T, VF | `flash_TVF` | 同上 |
| `self.Pe_BaseOn` | P, VF | `flash_PVF` | 同上 |
| `self.DP_BaseOn` | P, duty | `flash_DP` | 直接得 T/VF |
| `self.DT_BaseOn` | T, duty | `flash_DT` | 直接得 P/VF |

## Run() 标准五段式

```python
def Run(self):
    # 1) 能量流与输入校验
    self.set_duty()
    self.XI_mol = self.FFin.XI_mol
    self.F_mol = self.FFin.F_mol
    if self.F_mol == 0:
        self.feedback("warn", "输入流股没有流量", 30501)
        return False, {}
    if sum(self.XI_mol) < 0.000001:
        self.feedback("warn", "输入流股没有输入组分", 30500)
        return False, {}
    if len([i for i in [self.T, self.P_in, self.VF, self.duty] if i is None]) > 2:
        self.feedback("error", "输入条件给定不足", 40500)
        return False, {}

    # 2) 初值 warm start:条件有变化 → 保留旧初值;T/P/VF/duty 全未变时,
    #    组成未变 → Comp_filter(K0) 复用;组成变了 → init_starter() 清空
    #    (同时 self.P = self.P_in 保持基类兼容字段同步)
    # 3) 组分过滤(进闪蒸前必做):
    self.XI_mol, self._Is0, self.Not0 = Comp_filter(np.array(self.XI_mol))

    # 4) 按 *_BaseOn 分派闪蒸(见上表),结果存 self.Flash_core;
    #    初值 T0/P0/K0/VF0 与 SkipIndex=self._Is0 一并传入
    # 5) 回写:
    #    Flash_core → self.T/P_in/VF/XI_mol/LXI_mol/VXI_mol/K
    #    (VF>=1 时 LXI_mol 置零向量,VF<=0 时 VXI_mol 置零向量)
    #    get_F_LV_JB → FV_mol/FL_mol;压降/公用工程/密度等派生量
    #    Comp_restore 把 XI_mol/VXI_mol/LXI_mol/K 恢复到全组分坐标
    #    getReaction()(若有反应)→ set_value()
    return True, self.result
```

初值管理(warm start 语义,注意方向):

- `init_starter()`:`P0/T0/K0/VF0/XI0/duty0` 全部置 `None`。
- `set_value()` 开头保存本轮收敛值作下轮初值:`self.K0 = self.K; self.VF0 =
  self.VF; self.P0 = self.P_in; self.T0 = self.T; self.XI0 = self.XI_mol;
  self.duty0 = self.duty`。
- 复用规则:输入条件(T/P/VF/duty)有变化时,**保留**旧初值作为新工况的迭代
  起点(不清空——流程迭代中条件每轮微变,清空会废掉 warm start);四个条件
  全部未变时:组成也未变 → 直接复用
  (`self.K, _Is0, Not0 = Comp_filter(np.array(self.K0))`);
  组成变了 → `init_starter()` 清空。
- 方法包或组分集(活跃组分数/SkipIndex)变化后严禁复用旧 `K0`。

## 反应计算惯用法 getReaction

反应以**入口流股口径**计算(组分摩尔流量、相体积流量取自 `FFin`,`VF=0`),
结果只更新反应相关字段,**不回改闪蒸得到的 `F_mol`/`XI_mol`/`VF` 状态量**:

```python
def getReaction(self):
    self.F_vol = self.FFin.F_vol
    if self.RList:
        (self.FXI_mol_out, self.FL_mol, self.LXI_mol, A,
         self.FV_mol, self.VXI_mol) = self.Reaction_Base(
            comp_list=self.Data.CAS,
            FXI_mol_L=self.FFin.FLXI_mol,
            FXI_mol_V=self.FFin.FVXI_mol,
            F_vol_L=self.FFin.FL_vol,
            F_vol_V=self.FFin.FV_vol,
            RP=self.P_in, RT=self.T, VF=0)
```

## 出口流股回写与 Flow 契约

`set_value()` 把结果写到出口 Flow(通用契约的第三条输出通道在本族的落地),
连接能量流时还要**反向回写换热端温度**:

```python
self.FDout.F_mol = self.FV_mol; self.FDout.P_in = self.P_in
self.FDout.T = self.T; self.FDout.XI_mol = self.VXI_mol; self.FDout.GasRat = 1
self.FWout.F_mol = self.FL_mol; self.FWout.P_in = self.PW_out
self.FWout.T = self.T; self.FWout.XI_mol = self.LXI_mol; self.FWout.GasRat = 0.0
if self.DutyIn:
    self.DutyIn.T0 = self.T
    self.DutyIn.T1 = self.T + 2.0 if self.duty > 0.0 else self.T - 2.0
```

Flow 常用字段——读进口:`XI_mol`、`F_mol`、`FXI_mol`、`FLXI_mol`/`FVXI_mol`、
`FL_vol`/`FV_vol`、`F_vol`、`FH`(焓流)、`P_out`(上游出口压力)、`T`;
写出口:`F_mol`、`P_in`、`T`、`XI_mol`、`GasRat`。

`result` 键示例(格式契约见 `cslab-module-contract`):出口温度、出口压力、
汽化率、热负荷、压降等,中文键 + `{"value", "unitType"}`。

## FlashTank 家族禁止事项

1. 不发明词汇表之外的同义属性名(如 `self.temp` 替代 `self.T`)。
2. 不重写/复制基类算法(闪蒸迭代、相焓分支、Rachford-Rice 等)。
3. 不混用全组分坐标与活跃组分坐标(`Comp_filter` 之后、`Comp_restore` 之前,
   一切相组成都在活跃坐标;`SkipIndex=self._Is0` 恒传)。
4. 汽化率边界不处理就输出(VF=0/1 时对应相组成必须置零向量)。
