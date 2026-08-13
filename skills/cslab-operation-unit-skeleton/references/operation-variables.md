# CSLab operation 变量词汇表

本表是 CSLab 模块中流股、闪蒸、能量、组分坐标和常见模块族变量的权威定义。
模板或经验证的同族契约可覆盖默认端口名，但不得在代码中自行发明同义字段。

## 目录

- [项目开发文档来源与使用优先级](#项目开发文档来源与使用优先级)
- [适用范围继承规则](#适用范围继承规则)
- [模块自定义变量发现规则](#模块自定义变量发现规则)
- [通用状态与流股](#通用状态与流股)
- [热力学与能量](#热力学与能量)
- [闪蒸、组成坐标与求解控制](#闪蒸组成坐标与求解控制)
- [端口和模块族专用变量](#端口和模块族专用变量)
- [Data 上下文字段](#data-上下文字段)
- [容器状态与尺寸命名](#容器状态与尺寸命名)
- [动态速率、累计量与容器能量命名](#动态速率累计量与容器能量命名)
- [画布与仪表几何属性](#画布与仪表几何属性)
- [文章 427 冲突与核实清单](#文章-427-冲突与核实清单)

## 项目开发文档来源与使用优先级

项目开发文档《属性命名》（文章 ID 427，
`https://cslab.oberyun.com:8400/article?id=427`）提供容器、动态状态、累计量及画布几何
属性的规范候选名称。本表保留其原始大小写和历史拼写，并标明适用范围与待核实项。
该文章是项目命名规范，不是具体模板的 `moduleT` API 响应，也不证明某个变量已在后台
配置。

变量证据冲突时按以下顺序处理：当前模板详情 API → 已验证的同族运行契约 → 本文章的
命名规范 → Agent 推断。文章字段只有经具体模板 API 复核后，才能进入后台变量目录的
“已确认后台属性”；不得仅凭文章名称新增构造形参、落库属性或节点。

## 适用范围继承规则

- 表中“适用范围”包含 `Flow` 时，`Flow` 表示基础字段的来源层级，不表示该字段只允许
  Flow 对象使用。项目中的其他业务模块视为 Flow 语义的扩展，均继承这些字段的名称、
  含义、单位和组分坐标规则，包括 operation、dynamic、control、design、
  chemical-principle 等模块族。
- `Flow 完整坐标` 同样适用于模块对外保存和发布的对应字段；算法内部若使用活跃局部
  坐标，必须遵守本表的 `Comp_filter` / `Comp_restore` 边界规则。
- 适用范围仅标注 `Flash`、`FlashTank`、`Data` 或其他专用族且不包含 `Flow` 时，才按
  对应专用契约限制使用，不得因“模块是 Flow 扩展”而把专用字段扩散到所有模块。

## 模块自定义变量发现规则

本表不穷举开发者为具体模块新增的业务变量。遇到表外变量时，加载
[`cslab-module-develop`](../../cslab-module-develop/SKILL.md)，按其开发总入口流程从
开发者提示词、模板 `moduleProp` / `moduleNode`、负责范围内公开源码和开发者确认中建立
需求事实表及“模板属性 ↔ 构造形参/实例属性”对照表，据此确认变量名、含义、单位、
输入输出角色和数据来源。不得因为本表没有收录就判定变量不存在，也不得把单个模块的
自定义变量提升为所有模块的公共字段。

通过 API 或后台配置确认的模板变量统一查阅
[`cslab-modulet-api/references/backend-template-variables.md`](../../cslab-modulet-api/references/backend-template-variables.md)。
该目录持续保存模板变量名、简称、描述、单位、方向、模板范围和证据状态；本表不重复定义
其中的模块专用变量。

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
| `Diameter` | 容器直径 | m；仅 Vessel/FlashTank 契约 |
| `HHL` | FlashTank 液位输出 | 按模板单位 |
| `PW_out` | 含静液柱修正的罐底出口压力 | Pa |
| `mode` | 设计/校核模式 | `0` 设计，`1` 校核；仅对应家族 |
| `RList` | 反应 ID 列表 | 仅 ReactionBase 契约 |
| `Data` | 项目物性数据上下文 | 对象 |
| `comp` | 当前模块从 `Data.comp` 保存的组分元数据引用 | 仅目标家族明确提供时使用 |
| `Method_bag` | 方法包 ID | 字符串/ID |

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

## 容器状态与尺寸命名

以下名称来自文章 427，适用于容器、储罐、塔器或动态设备的候选契约。只在目标模板、
已验证同族契约或开发者确认存在对应能力时使用。

| 变量 | 含义 | 单位/取值 | 适用范围与说明 |
|---|---|---|---|
| `LL` | 百分比液位 | `%` | 容器液位展示；与实际液位 `LA` 区分 |
| `LA` | 实际液位 | m | 容器动态状态或输出 |
| `Height` | 罐体或塔器高度 | m | Vessel、储罐或塔器模板 |
| `Volume` | 罐体总体积 | m3 | 容器几何属性 |
| `Volume_G` | 罐内液面以上空间体积 | m3 | 文章称“罐液上体积”；气相空间语义需结合模型确认 |
| `Area_L` | 当前液面面积 | m2 | 可随液位或容器姿态变化 |
| `Area` | 容器底面积 | m2 | 文章中重复出现，具体几何含义须按模板确认 |
| `Type_V` | 容器类型 | 枚举 | 圆柱、球形、椭圆封头、半球封头等 |
| `Gesture` | 容器姿态 | 枚举 | 立式或卧式 |
| `LHMP` | 液位高测点 | m | 模板报警或测点属性 |
| `LLMP` | 液位低测点 | m | 模板报警或测点属性 |
| `PW` | 罐底压力 | Pa | 液柱压差修正后的罐底压力；与 `PW_out` 的关系须按模板确认 |

文章同时列出的 `T`、`P_in`、`P_out` 和 `Diameter` 已在本表前述权威行定义，不在此
重复定义。用于容器模块时，`T` 表示罐内温度；`P_in` 的对象语义仍须按冲突清单核实。

## 动态速率、累计量与容器能量命名

| 变量 | 含义 | 单位 | 适用范围与说明 |
|---|---|---|---|
| `TRAT` | 温度变化率 | 待模板确认 | 动态状态诊断或输出；文章未给出时间基准 |
| `PRAT` | 压力变化率 | 待模板确认 | 动态状态诊断或输出；文章未给出时间基准 |
| `FRAT` | 流量变化率 | 待模板确认 | 动态状态诊断或输出；需确认摩尔、质量或体积基准 |
| `LRAT` | 液位变化率 | 待模板确认 | 动态状态诊断或输出；文章未给出时间基准 |
| `FY_mol` | 摩尔汽化量或汽化摩尔流率 | kmol/s | 原文写“摩尔汽化量”，单位显示为流率，须按方程确认 |
| `FY_mass` | 质量汽化量或汽化质量流率 | kg/s | 原文写“质量气化量”，单位显示为流率，须按方程确认 |
| `WL_mass` | 液相累计质量 | kg | 动态库存状态 |
| `WL_mol` | 液相累计物质的量 | kmol | 动态库存状态 |
| `WV_mass` | 汽相累计质量 | kg | 动态库存状态 |
| `WV_mol` | 汽相累计物质的量 | kmol | 动态库存状态 |
| `Ka_Cont` | 散热系数 | 待模板确认 | 保留文章大小写；不得默认等同现有历史名 `KA_Cont` |
| `Qs` | 散热量 | J | 文章定义为累计能量；若算法表示散热功率应使用经确认的 W 口径 |
| `Q` | 外部加热量 | J | 文章定义为累计能量；不得自动当作热负荷或热流率 |
| `H_all` | 焓累计量 | J | 容器累计能量状态 |

文章同时列出的 `Density_mass`、`Density_mol`、`VXI_mol` 和 `LXI_mol` 已在本表前述
权威行定义；组成字段继续严格遵守完整坐标与 Flash 活跃坐标的边界，不另建同义字段。

## 画布与仪表几何属性

以下字段属于前端画布布局、仪表连接或设备展示数据，不是物理模型的状态方程变量。
算法只有在模板明确注入、读取或回写这些字段时才使用。

| 变量 | 含义 | 单位/坐标 | 注意事项 |
|---|---|---|---|
| `distance_h` | 模块距离地面的高度 | 按画布或模板坐标 | 不等同于容器液位或设备高度 |
| `distance_d` | 仪表连接点到流股入口点的线长 | 按画布或模板坐标 | 仅仪表类连接语义 |
| `distance_x` | 仪表连接点到流股入口点的 X 轴距离 | 按画布或模板坐标 | 与下方流股几何同名，须结合对象类型 |
| `distance_y` | 仪表连接点到流股入口点的 Y 轴距离 | 按画布或模板坐标 | 与下方流股几何同名，须结合对象类型 |
| `Rotate` | 设备旋转角度 | 待模板确认 | 所有设备的展示旋转属性 |
| `LineLenght` | 通过虚线连接到流股的所属线长 | 按画布或模板坐标 | 保留文章历史拼写，不擅自改为 `LineLength` |
| `xdistance_x` | 流股起点与终点的 X 轴距离 | 按画布或模板坐标 | 文章原始名称 |
| `ydistance_y` | 流股起点与终点的 Y 轴距离 | 按画布或模板坐标 | 文章原始名称 |

## 文章 427 冲突与核实清单

| 字段 | 冲突或缺口 | 使用规则 |
|---|---|---|
| `P_in` | 文章同时描述罐内压力和入口压力 | 按当前模板、设备边界和方程对象确定，不建立两个同名状态副本 |
| `Area` | 文章两次写作底面积，且未区分几何场景 | 以目标容器模型和模板描述为准 |
| `PW` / `PW_out` | 文章使用 `PW`，现有 FlashTank 契约使用 `PW_out` | 不设通用别名；按目标模板严格同名 |
| `Ka_Cont` / `KA_Cont` | 大小写不一致 | Python 名称区分大小写，禁止静默归一化 |
| `Qs` / `Q` | 原文单位为 J，但名称可能被误用作热流率 | 先确认累计能量还是功率；功率口径不得沿用 J |
| `TRAT/PRAT/FRAT/LRAT` | 原文未给出时间单位 | API 或开发者未确认前不得猜成每秒、每分钟或每小时 |
| `distance_x/distance_y` | 同名字段可描述仪表或流股几何 | 结合模板所属对象和描述解释，不能跨对象复用数值 |
| `LineLenght` | 疑似历史拼写 | 模板存在时保留严格同名；新模板命名需由开发者确认后配置 |
| `FFin/FDout/FWout` | 文章将其列为进料、汽相和液相端口 | 仅适用于采用该端口契约的模块族，不能扩散为所有模块固定端口 |
