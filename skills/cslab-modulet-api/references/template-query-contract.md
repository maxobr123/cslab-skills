# moduleT 查询与模板数据契约

## 接口

| 接口 | 方法 | 用途 |
|---|---|---|
| `moduleT/deviceType/` | GET | 设备类型分类字典 |
| `moduleT/list/` | GET | 模板列表，查询参数含 `module_type`、`isUser` |
| `moduleT/?pk=<id>` | GET | 单模板详情 |
| `moduleT/pyTemp?pk=<id>&class_name=<类名>` | GET | 模板 Python 骨架，详见维护 reference |
| `moduleT/` | POST/PUT/DELETE | 模板、属性和节点维护，详见维护 reference |

模板 id、属性 id、节点 id 通常为 32 位无横线 hex，不具有业务含义。

## 查询流程

1. `moduleT/list/` 按名称、label、描述和算法名收集候选；多个候选完整展示给开发者。
2. 选定后只请求必要的一次 `moduleT/?pk=<id>`。详情 GET 会把不在可选集中的部分库值
   归一化并回写，不能当成无副作用的纯查询反复调用。
3. 核对 `startFun`、四个算法槽位、`moduleProp`、`moduleProp7` 和 `moduleNode`。
4. `{describe, value}` 字段取当前值；下拉字段的 `value=[当前值, 全部候选]`，不能把
   候选全集报告为模板参数。
5. 单位为空、变量疑似拼写错误或配置冲突只标记“后台当前配置/待确认”，不自行改写事实。

## deviceType 与列表

`deviceType` 的 `data` 是按 `rank` 排序的 `[{"mt_pk", "device_type", "rank"}]`。
它是工具栏设备类型，与模板 `classify`、`family` 为不同维度。

模板列表常用字段：`t_module_pk`、`name`、`describe`、`label`、`classify`、
`creator`、`creator_id`、`isOperator`。写入前必须确认 `isOperator`。

## 模板详情

详情顶层通常为：

```json
{
  "module": {},
  "moduleProp": [],
  "moduleProp7": [],
  "moduleNode": [],
  "modulePropS": [],
  "moduleComp": []
}
```

### module

关键字段包括 `t_module_pk`、`name`、`describe`、`label`、`name_prefix`、`rank`、
`startFun`、`classify`、`family`，以及：

| 字段 | 模式 |
|---|---|
| `steady_module` | 稳态 |
| `dynamic_module` | 动态 |
| `chemical_principle_module` | 化工原理 |
| `design_module` | 设计 |

算法槽位可使用 `<目录>.<文件名>`、`<目录>.<文件名>;<类名>`（也兼容既有分隔符），或
已确认的绝对 `.py/.pyd/.so` 路径。scheduler 按路径导入后取得类，必须核对类名。

### moduleProp

关键字段及语义：

| 字段 | 含义 |
|---|---|
| `t_prop_pk` | 属性 id |
| `name` | 与构造形参或实例属性同名的 Python 变量名 |
| `describe` / `desc` | 中文简称和描述 |
| `classify` / `classify2` | 基本数据类型和复合元素类型 |
| `value` | 默认值；列表配维度字段，枚举通常含当前值与候选 |
| `is_input` | 输入/输出语义；不等于服务端下发过滤条件 |
| `unitType` / `unit` / `opt_unit` | 展示单位契约；注入本身不换算，默认值必须为 SI |
| `source` / `relyOn` / `relyOn7` | 枚举源和联动 |
| `hide` / `rank` / `style_info` | 显示与排序 |
| `cold_state` / `calculate_state_judgement` | 状态保存判断 |

已确认 `classify` 编码：`0` 整数、`1` 浮点数、`2` 字符串、`3` 列表、`4` 枚举、
`5` 布尔、`6` 组分、`7` 引用赋值、`8` 反应、`9` 标准枚举；`8/9` 通常不可手选。
列表 `classify2` 常见 `0/1/2/5`，引用类常见 `0` 赋值、`1` 引用、`2` 引用实例、
`3` 赋值多、`4` 引用多。

已确认特殊注入包括：组分系数生成 `{属性名}_UnitType` 并转数组；列表/反应类按当前类型
转运行对象；`classify=73` 可生成 `{属性名}__formula`，`74` 不生成。`is_input` 不参与
服务端下发过滤，输出属性也可能挂到实例。仍须以当前详情和运行控制器为准。

### moduleNode

| 字段 | 含义 |
|---|---|
| `t_node_pk` | 节点 id |
| `name` | 与构造形参同名的节点名 |
| `code` | FLOW、Energy、VALVE、singleNode 等节点类型 |
| `interface` | 进/出 |
| `phase` | 水相、液相、汽相、汽液相等 |
| `seat` / `point` / `rank` | 位置、坐标和排序 |

FLOW/Energy 按名称注入对象，未连接时为 `None`；聚合节点和其他类型的注入规则必须结合
实际控制器与模板确认。当前已知特殊聚合名包括 `VALVE -> Valve_Data_list`、
`REGRESSION -> RegressionList`、`OIL -> Oil_Blends`；`Flow_list` 只聚合 FLOW 节点。

## 项目实例与本地源码边界

模板定义来自 moduleT；具体项目属性值、连接和执行顺序来自
`POST obtainData/CalculateData/`。payload 至少含 `pro` 和 `callow_item`，其他字段由当前
运行入口决定。入口文件名不是平台固定契约，必须在当前项目检索确认。

服务器画布数据可以驱动本地运行，但网页服务器算法不会替代本地文件，网页结果也不能
证明本地 `.py` 被加载。项目实例缺少的模板语义仍以详情 API 为准。
