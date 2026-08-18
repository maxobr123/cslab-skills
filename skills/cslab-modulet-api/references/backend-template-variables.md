# CSLab 后台模板变量目录

本目录记录开发者通过 `moduleT` API 或后台模板界面确认的变量名、中文含义和模板范围，
供后续模块开发复用。它是“后台配置事实”的持续目录，不替代具体模板详情；开发某个模块时，
仍以本次 `GET moduleT/?pk=<t_module_pk>` 返回的数据为最终契约。

## 持续维护规则

1. 开发者触发模板 API 查询并取得新的 `moduleProp` 或 `moduleNode` 后，逐项与本目录
   比较，并在当前开发任务内补充或修正目录。
2. 优先记录完整详情字段：模板 ID、模板名称、设备类型、属性/节点 ID、`name`、
   `describe`、`desc`、`classify`、`is_input`、`unitType`、`unit`、
   默认值、节点 `code/interface/phase`、获取日期和来源。
3. 只记录 API 响应或开发者提供的后台证据中实际出现的内容；截图未显示、响应未返回的
   字段标记“待补充”，不得根据英文名猜单位、方向、默认值或物理含义。
4. 以 `(t_module_pk, t_prop_pk)` 或 `(t_module_pk, t_node_pk)` 标识一条后台配置。
   不同模板可使用同一个 `name` 表示不同业务语义，必须按模板分别保留，不能互相覆盖。
5. 只有多个模板的名称、含义、单位和坐标规则一致且经开发者确认后，才能把变量提升为
   公共变量；模块专用变量不得写成所有模块的通用契约。
6. 目录更新后先修改 `.opencode/skills/skills/` 管理源，运行官方 Skill 校验，再同步
   `.agents/skills/` 并比较 SHA-256；按项目既定 Skill 管理流程提交和推送。
7. 不记录 JWT、Authorization 请求头、账号信息或项目实例中的敏感业务值；目录只保存
   模板结构、变量契约、来源标识和确认状态。
8. 开发方案提出但尚未在后台配置，或配置后尚未通过
   `GET moduleT/?pk=<t_module_pk>` 详情复核的变量，只能保留在当前技术方案的“待配置
   后台变量清单”中，不得加入下方“已确认后台属性”，也不得用于算法编码。
9. 写接口成功、列表摘要或字段不完整的截图不能代替详情复核。只有变量名、类型、单位、
   方向、默认值、模板范围及节点契约与确认方案一致后，才可登记为已确认配置。

## 已确认后台属性

### Tank_Opensgy

以下契约来自 2026-08-18 的 `GET moduleT/?pk=03c4932540684dc785cea97900fd6ef9`
详情响应,替代此前只有五个名称的截图记录。

- 模板名/标识:`Tank_Opensgy`
- 设备类型:`水箱`
- 启动函数:`Run`
- 动态算法:`dynamic.Dtank_Opensgy,Dtank_Open`
- `moduleProp` 共 26 项;只有 `Method_bag` 的 `is_input=是`,其余均为 `否`。运行时仍会
  下发所有属性,不得把 `is_input=否` 解释为“不注入”。
- 所有属性的 `calculate_state_judgement=否`;仅 `LA`、`LL`、`H_all` 的
  `cold_state=是`。

| `name` | 中文简称/描述 | 类型 | 默认值 | 单位类型/单位 | 方向 | 排序 | 冷态 |
|---|---|---|---|---|---|---:|---|
| `Method_bag` | 方法包 | enum(4),元素 str(2) | 空 | 未配置 | 输入 | 1 | 否 |
| `Diameter` | 底面直径 | float(1) | `1.0` | Length / meter | 输出 | 2 | 否 |
| `Height` | 罐高 | float(1) | `2.0` | Length / meter | 输出 | 2 | 否 |
| `LRAT` | 液位变化率 | float(1) | `0.1` | 未配置 | 输出 | 3 | 否 |
| `LHMP` | 液位高测点 | float(1) | `2.0` | Length / meter | 输出 | 3 | 否 |
| `LLMP` | 液位低测点 | float(1) | `0.0` | Length / meter | 输出 | 3 | 否 |
| `PRAT` | 压力变化率 | float(1) | `0.1` | 未配置 | 输出 | 5 | 否 |
| `TRAT` | 温度变化率 | float(1) | `0.1` | 未配置 | 输出 | 5 | 否 |
| `P_in` | 罐内压力 | float(1) | `101325.0` | Pressure / Pa | 输出 | 5 | 否 |
| `T` | 罐内温度 | float(1) | `298.15` | Temperature / K | 输出 | 5 | 否 |
| `WL_mol` | 液相累积量摩尔/液相累积量 | float(1) | `1.0` | Moles / kmol | 输出 | 100 | 否 |
| `Fs_mass` | 溢流流量 | float(1) | `0.0` | Mass flow / kg/sec | 输出 | 101 | 否 |
| `WL_mass` | 液相累积量质量 | float(1) | `0.0` | Mass / kg | 输出 | 101 | 否 |
| `FY_mol` | 蒸发摩尔量 | float(1) | `0.0` | Mole flow / kmol/sec | 输出 | 103 | 否 |
| `Fs_mol` | 溢出摩尔量 | float(1) | `0.0` | Mole flow / kmol/sec | 输出 | 103 | 否 |
| `KA_Cont` | 散热常数 | float(1) | `0.0` | 未配置 | 输出 | 103 | 否 |
| `LA` | 实际液位 | float(1) | `0.0` | Length / meter | 输出 | 110 | 是 |
| `Density_mass` | 液相密度 | float(1) | `800.0` | Mass density / kg/cum | 输出 | 110 | 否 |
| `LL` | 百分比液位 | float(1) | `0.0` | 未配置 | 输出 | 110 | 是 |
| `H_all` | 总焓 | float(1) | `0.0` | 未配置 | 输出 | 110 | 是 |
| `HL_mol` | 摩尔焓 | float(1) | `0.1` | 未配置 | 输出 | 140 | 否 |
| `HL_mass` | 质量焓 | float(1) | `0.1` | 未配置 | 输出 | 142 | 否 |
| `CP_mass` | 质量热熔 | float(1) | `0.1` | 未配置 | 输出 | 142 | 否 |
| `distance_h` | 距地面高度 | float(1) | `0.0` | 未配置 | 输出 | 1000 | 否 |
| `VXI_mol` | 汽相摩尔分率 | comp(6) | `"0"` | 未配置 | 输出 | 999999 | 否 |
| `LXI_mol` | 液相摩尔分率 | comp(6) | `"0"` | 未配置 | 输出 | 999999 | 否 |

## 已确认后台节点

| `t_node_pk` | `name` | 含义 | 节点类型 | 方向 | 相态 | 模板范围 |
|---|---|---|---|---|---|---|
| `e8df3093e528416889091e40525daed1` | `FFin` | 进口 | 流股节点 | 进 | 汽液相 | `Tank_Opensgy` (`03c4932540684dc785cea97900fd6ef9`) |
| `fc38b7b9c94841ee9ab3e785846a53a3` | `FWout` | 出口 | 流股节点 | 出 | 汽液相 | `Tank_Opensgy` (`03c4932540684dc785cea97900fd6ef9`) |

## 当前配置待确认项

- `LRAT`、`PRAT`、`TRAT`、`KA_Cont`、`LL`、`H_all`、`HL_mol`、`HL_mass`、
  `CP_mass`、`distance_h`、`VXI_mol`、`LXI_mol` 的单位类型或单位在详情中为空;开发时
  不得自行把推测单位写成后台事实。
- `CP_mass` 的后台中文简称和描述均为“质量热熔”,疑似“质量热容”的文字错误,但在
  开发者确认并完成后台修改前必须保留原文。
