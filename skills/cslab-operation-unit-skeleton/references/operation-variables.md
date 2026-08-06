# CSLab operation 变量词汇表

本表是 operation 业务模块中流股、闪蒸、能量、组分坐标和常见模块族变量的权威定义。
模板或经验证的同族契约可覆盖默认端口名，但不得在代码中自行发明同义字段。

## 通用状态与流股

| 变量 | 含义 | 单位/坐标 | 适用范围 |
|---|---|---|---|
| `T`, `T0` | 当前温度、求解初值 | K | Flow、Flash、operation |
| `P`, `P0` | 闪蒸内部压力、求解初值 | Pa | Flash |
| `P_in` | 当前流股或单元计算压力 | Pa | Flow、operation |
| `P_out` | 当前 Flow 的出口压力，下游作为上游边界读取 | Pa | Flow |
| `Pressure_drop` | 压降，具体正负号按模块族方程确认 | Pa | operation |
| `F_mol`, `F_mass`, `F_vol` | 总摩尔、质量、体积流量 | kmol/s；kg/s；m3/s | Flow |
| `FXI_mol`, `FXI_mass`, `FXI_vol` | 各组分摩尔、质量、体积流量 | kmol/s；kg/s；m3/s | Flow 完整坐标 |
| `XI_mol`, `XI_mass`, `XI_vol` | 总流股摩尔、质量、体积分率 | 无量纲 | Flow 完整坐标 |
| `GasRat`, `VF`, `VF0` | 气相摩尔分率、业务别名、求解初值 | 0 到 1 | Flow、Flash |
| `XI0`, `duty0` | 入口组成、热负荷的暖启动记录 | 完整组分坐标；W | FlashTank 等已验证家族 |
| `T_init`, `P_init`, `duty_init` | 输入条件原始记录；部分家族用 `P_init` 判断压力是否为输入 | K；Pa；W | FlashTank 等模板驱动 operation |
| `V_mol`, `L_mol`, `Sol_mol` | 气、液、固相摩尔分率 | 0 到 1 | Flow |
| `FV_mol`, `FL_mol`, `FS_mol` | 气、液、固相摩尔流量 | kmol/s | Flow、operation |
| `FV_mass`, `FL_mass`, `FS_mass` | 气、液、固相质量流量 | kg/s | Flow |
| `FV_vol`, `FL_vol`, `FS_vol` | 气、液、固相体积流量 | m3/s | Flow |
| `FVXI_mol`, `FLXI_mol`, `FSXI_mol` | 各相组分摩尔流量 | kmol/s | Flow 完整坐标 |
| `FVXI_mass`, `FLXI_mass`, `FSXI_mass` | 各相组分质量流量 | kg/s | Flow 完整坐标 |
| `VXI_mol`, `LXI_mol`, `SXI_mol` | 气、液、固相摩尔组成 | 无量纲 | Flow 中为完整坐标；Flash 中为活跃坐标 |
| `VXI_mass`, `LXI_mass`, `SXI_mass` | 气、液、固相质量组成 | 无量纲 | Flow 完整坐标 |
| `Phase` | 流股相态标识 | 枚举/字符串 | Flow |

相前缀规则：`V` 表示 vapor，`L` 表示 liquid，`S` 表示 conventional solid，
`NCS` 表示 nonconventional solid；`F` 表示流量，`XI` 表示组成。

## 热力学与能量

| 变量 | 含义 | 单位 | 适用范围 |
|---|---|---|---|
| `H_mol`, `HL_mol`, `HV_mol`, `HS_mol` | 总体、液相、气相、固相摩尔焓 | J/kmol | Flow、Flash |
| `H_mass`, `HL_mass`, `HV_mass`, `HS_mass` | 对应质量比焓 | J/kg | Flow |
| `S_mol`, `SL_mol`, `SV_mol` | 总体、液相、气相摩尔熵 | J/(kmol*K) | Flow |
| `S_mass`, `SL_mass`, `SV_mass` | 对应质量比熵 | J/(kg*K) | Flow |
| `G_mol`, `GL_mol`, `GV_mol` | 总体、液相、气相摩尔 Gibbs 能 | J/kmol | Flow |
| `G_mass`, `GL_mass`, `GV_mass` | 对应质量比 Gibbs 能 | J/kg | Flow |
| `CP_mol`, `CPL_mol`, `CPV_mol` | 总体、液相、气相摩尔定压热容 | J/(kmol*K) | Flow |
| `CP_mass`, `CPL_mass`, `CPV_mass` | 对应质量定压热容 | J/(kg*K) | Flow |
| `Density_mol`, `DensityL_mol`, `DensityV_mol` | 总体、液相、气相摩尔密度 | kmol/m3 | Flow |
| `Density_mass`, `DensityL_mass`, `DensityV_mass` | 对应质量密度 | kg/m3 | Flow |
| `MW`, `MW_avg`, `MWL_avg`, `MWV_avg` | 组分及总体、液相、气相平均分子量 | kg/kmol，数值等于 g/mol | Flow、Data |
| `FH`, `FHL`, `FHV`, `FHS` | 总体、液相、气相、固相焓流 | W | Flow、Flash |
| `FHin` | 入口焓流 | W | duty 闪蒸 |
| `Duty`, `duty` | 指定热负荷；大小写不是通用别名 | W | 按目标模块族确认 |
| `RDuty` | 根据出口与入口焓流得到的实际净热负荷 | W | operation |
| `target_duty` | duty 闪蒸目标净热负荷 | W | `flash_DP`, `flash_DT` |
| `DutyIn` | 能量流对象，常用字段为 `Duty`, `T0`, `T1` | 对象 | 仅模板明确提供时使用 |

## 闪蒸、组成坐标与求解控制

| 变量 | 含义 | 单位/坐标 |
|---|---|---|
| `ZI` | 闪蒸进料摩尔组成 | 活跃局部坐标，无量纲 |
| `XI_mol_in` | 业务单元过滤后的进料摩尔组成 | 活跃局部坐标，无量纲 |
| `LXI_mol`, `VXI_mol` | 闪蒸液相、气相组成 | Flash 内为活跃局部坐标 |
| `K`, `K0` | 汽液相平衡 K 值及暖启动值 | 活跃局部坐标，无量纲 |
| `A` | 闪蒸结果的相平衡非理想修正字段 | 无量纲；不得当作 `K` |
| `Is0`, `_Is0`, `SkipIndex` | 被过滤组分在完整项目坐标中的全局索引 | 整数索引列表 |
| `Not0` | 未被过滤组分在完整项目坐标中的全局索引 | 整数索引列表 |
| `Flash_core` | `Instantiation=True` 的完整闪蒸结果对象 | 对象 |
| `BubT`, `DewT`, `BubP`, `DewP` | 泡点/露点温度和压力 | K；Pa |
| `T0`, `P0`, `VF0`, `K0` | 温度、压力、汽化率、K 值暖启动 | 对应变量单位 |
| `DT` | 求解或差分步长配置 | 依目标算法；不是动态时间步的通用保证 |
| `DOA`, `abs_DOA` | 相对、绝对收敛控制 | 无量纲/随残差定义 |
| `K_time` | 最大迭代次数 | 次 |
| `iteration_factor` | 迭代松弛/加速因子 | 无量纲 |
| `iterative_method` | 迭代方法名，如 `Wegstein` | 字符串 |

`Comp_filter(full_xi)` 返回活跃组成、跳过索引和保留索引；`Comp_restore` 才能把
Flash 活跃向量恢复为 Flow 完整坐标。不得仅用 `SkipIndex` 替换 `Is0/Not0` 中的一半。

## 端口和模块族专用变量

| 变量 | 含义 | 适用范围 |
|---|---|---|
| `Fin`, `Fout` | 入口 Flow、总体出口 Flow | 从零开发通用 operation 的默认语义名 |
| `FVout`, `FLout` | 纯气相出口、纯液相出口 Flow | 从零开发气液分离单元的默认语义名 |
| `Flow_list` | 多流股聚合注入列表 | 模板声明该形参时使用 |
| `FFin`, `FDout`, `FWout` | FlashTank 进料、气相出口、液相出口 | 仅 FlashTank 家族；实际相语义仍需模板确认 |
| `Input_type1/2`, `Input_value1/2` | 两组业务规格类型和值 | FlashTank 等模板驱动 operation |
| `TP_BaseOn`, `Te_BaseOn`, `Pe_BaseOn`, `DP_BaseOn`, `DT_BaseOn` | 已确认规格组合的分派标志 | Flash-capable operation |
| `Utility` | 公用工程配置 | 不是 Flow 端口 |
| `FU_mass`, `electricity`, `Price_U`, `CO2_emissions` | 公用工程耗量、电耗、费用、碳排 | `Public_F_P` 返回字段 |
| `Height`, `Diameter` | 容器高度、直径 | m；仅 Vessel/FlashTank 契约 |
| `LHMP`, `LLMP` | 高、低液位测点 | 按模板单位 |
| `HHL` | FlashTank 液位输出 | 按模板单位 |
| `PW_out` | 含静液柱修正的罐底出口压力 | Pa |
| `mode` | 设计/校核模式 | `0` 设计，`1` 校核；仅对应家族 |
| `RList` | 反应 ID 列表 | 仅 ReactionBase 契约 |
| `Data` | 项目物性数据上下文 | 对象 |
| `comp` | 当前模块从 `Data.comp` 保存的组分元数据引用 | 仅目标家族明确提供时使用 |
| `Method_bag` | 方法包 ID | 字符串/ID |
| `LRAT`, `PRAT`, `TRAT` | Vessel 液位、压力、温度相关设计/校核比率 | 按目标 Vessel 模板定义；不得跨家族猜单位 |

## Data 上下文字段

| 变量 | 含义 | 数据形态/使用规则 |
|---|---|---|
| `Data.comp` | 项目组分元数据 | 字典列表，常见键包括 `cas`、`alias` |
| `Data.CAS` | 项目组分 CAS 编号 | 完整项目组分坐标序列 |
| `Data.MW` | 项目组分分子量 | kg/kmol；完整坐标数组，可用 `Not0` 读取活跃视图 |
| `Data.PUW` | 公用工程配置集合 | 按 Utility ID 索引的字典 |
| `Data.binaryData_all` | 各方法包二元参数集合 | 键为方法包 ID；不得在业务层自行切片 |
| `Data.methodBag` | 方法包配置集合 | 使用 `Data.methodBag[Method_bag]` 选择当前配置 |
| `Data.ReactionData` | 项目反应数据集合 | 仅 ReactionBase 契约使用 |

缺省方法包 ID 的历史取法为 `list(Data.binaryData_all.keys())[0]`；新代码应优先使用
构造器明确注入的 `Method_bag`。共享 `Data` 不得为局部组分系统做破坏性裁剪。

FlashTank 的占位输出必须以目标模板为准；`HHL`、`Q`、`KA_Cont` 等名字不能扩散为
所有 operation 模块的通用字段。
