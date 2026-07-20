---
name: cslab-modulet-api
description: Use when querying or modifying CSLab module templates over HTTP - device type categories, template list, template detail (moduleProp/moduleNode), pyTemp skeleton generation, template CRUD, and the template-to-algorithm mapping fields.
---

# moduleT 模板接口契约

模板系统是"模块参数的唯一事实来源":一个模板(moduleT)定义了模块的基础信息、
参数属性(moduleProp)、连接节点(moduleNode),以及指向 `domain/operation/`
算法类的路径。开发算法前先通过这些接口取模板,推导构造契约。

## 地址与鉴权

- 基础前缀:`${CSLAB_SERVER_HOST}/cslab-server/`(变量名以实际 ENV 注入为准)。
- `moduleT/` 系列需要 JWT:请求头 `Authorization: JWT ${CSLAB_TOKEN}`
  (服务端取空格后第二段,前缀词不敏感)。
- 响应统一包装:`{"status": 200, "msg": "成功", "data": <业务数据>}`,先判
  `status` 再取 `data`。
- 401/接口不可达时向开发者确认 ENV,不要伪造数据继续。

## 接口总表

| 接口 | 方法 | 用途 |
|---|---|---|
| `moduleT/deviceType/` | GET | 设备类型分类字典 |
| `moduleT/list/` | GET | 模板列表(查询参 `module_type`、`isUser`) |
| `moduleT/?pk=<id>` | GET | 单模板详情:module/moduleProp/moduleNode |
| `moduleT/pyTemp?pk=<id>&class_name=<类名>` | GET | 由模板生成 Python 类骨架 |
| `moduleT/` | POST/PUT/DELETE | 模板/属性/节点增改删,body `{"item":..., "parameter": {...}}` |

模板 id(`t_module_pk`)及属性/节点 id 均为 32 位无横线 hex,无业务含义。

## deviceType 响应

`data` 为按 `rank` 升序的列表:`[{"mt_pk", "device_type", "rank"}]`。
这是工具栏分组用的"设备类型"字典,与模板自身的 `classify`(A 通用/B 特殊/…)、
`family` 是三个不同维度。

## list 响应

`data` 为模板列表,单项字段:

| 字段 | 含义 |
|---|---|
| `t_module_pk` | 模板 id |
| `name` / `describe` / `label` | 名称 / 描述 / 标识(匹配用) |
| `classify` | 已转中文:通用模块/特殊模块/数据模块/模板模块/实验模块/基类/电气模块/其他 |
| `creator` / `creator_id` | 创建者用户名 / 原始 id |
| `isOperator` | 当前用户是否有编辑权 |

按名称/标识匹配目标模板;多个候选时列给开发者选,不要自行猜测。

## 模板详情响应(核心)

`data` 顶层:

```json
{
  "module":      { },
  "moduleProp":  [ ],
  "moduleProp7": [ ],
  "moduleNode":  [ ],
  "modulePropS": [ ],
  "moduleComp":  [ ]
}
```

`modulePropS`/`moduleComp` 为预留空。字段值多为 `{"describe": 中文标签, "value": ...}`
形态;下拉类字段 `value = [当前值, 可选项列表]` 并带 `enumShow`/`enumReal` 映射。

**注意:该 GET 有回写副作用**——预览时会把不在可选集内的库值归一化并回写数据库,
不要把它当纯只读接口反复轰击。

### module(基础信息)

关键项:`t_module_pk`、`name`、`describe`、`label`、`name_prefix`、`rank`、
`startFun`(启动函数,默认 `Run`)、`classify`(模板类型)、`family`(设备类型),
以及**四个算法槽位**:

| 字段 | 计算模式 |
|---|---|
| `steady_module` | 稳态 |
| `dynamic_module` | 动态 |
| `chemical_principle_module` | 化工原理 |
| `design_module` | 设计 |

槽位值即算法路径,写法三选一:

1. `operation.<文件名>` —— 类名 = 点分末段(文件名与类名一致时);
2. `operation.<文件名>;<类名>` —— 类名与文件名不同时(分隔符 `; ； , ， |` 均可);
3. `.py/.pyd/.so` 绝对路径。

scheduler 按 `importlib.import_module("domain." + 路径)` 加载,再 `getattr` 取类。

### moduleProp(参数属性)

单个属性的关键字段:

| 字段 | 含义 |
|---|---|
| `t_prop_pk` | 属性 id(落库回写的键) |
| `name` | **英文变量名——与算法构造函数形参/实例属性同名注入** |
| `describe` / `desc` | 中文简称 / 描述 |
| `classify` | 数据类型编码:`0`整数 `1`浮点数 `2`字符串 `3`列表 `4`枚举 `5`布尔 `6`组分 `7`引用赋值 `8`反应 `9`枚举(标准);8/9 不可手选 |
| `classify2` | 复合类型的元素类型(列表:0/1/2/5;引用:0赋值 1引用 2引用实例 3赋值多 4引用多) |
| `value` | 默认值;列表型配 `dim_x`/`dim_y`/`list_data_label`;枚举型为 `[当前值, 可选列表]` |
| `is_input` | `是`=输入(候选构造参数);`否`=输出(Run 内赋同名实例属性以落库) |
| `unitType` / `unit` / `opt_unit` | 单位类型 / 单位 / 单位控制——**仅前端展示换算用,注入不换算,默认值必须是 SI 数值** |
| `source` | 枚举变量源(枚举类型时) |
| `relyOn` / `relyOn7` | 属性值联动控制 |
| `hide` / `rank` / `style_info` | 显示条件 / 排序 / 样式 |
| `cold_state` / `calculate_state_judgement` | 保存冷态 / 计算状态判断 |

注入的特殊处理:`classify=6` 且值种类为"系数"时额外生成 `{属性名}_UnitType` 并转
`np.array`;`classify` 以 `3` 开头的列表转 `np.array`/反应对象;仅 `classify=73`
(赋值多)生成 `{属性名}__formula` 注入,`74`(引用多)不生成。
**is_input 不参与下发过滤**(输出属性也会被打进计算数据挂到实例上),
方向语义靠约定维护。

### moduleNode(连接节点)

| 字段 | 含义 |
|---|---|
| `t_node_pk` | 节点 id |
| `name` | **节点名——与构造函数流股形参同名注入**(如 `FFin`/`FDout`) |
| `code` | 节点类型:`FLOW` 流股 / `Energy` 能量流 / `VALVE` 阀门 / `singleNode` 单节点等 |
| `interface` | `进` / `出` |
| `phase` | 相态:水相/液相/汽相/汽液相 |
| `seat` / `point` / `rank` | 位置 / 坐标 / 排序 |

注入规则:FLOW/Energy 节点按 `name` 注入 Flow/能量流实例;类形参含 `Flow_list`
时聚合注入字典列表(仅聚合 FLOW 流股节点);`VALVE→Valve_Data_list`、
`REGRESSION→RegressionList`、`OIL→Oil_Blends`;**未连接的 FLOW/Energy 节点
注入 `None`**。

## pyTemp 骨架生成

`GET moduleT/pyTemp?pk=<id>&class_name=<类名>` 返回按模板属性+节点生成的类骨架
(形参带类型标注与默认值)。局限:**无 `Data`/`Method_bag` 形参、无基类继承、
`Run` 为空桩**,只能当起点,必须按 `cslab-module-contract` 与所属族包
(如 `cslab-operation-skeleton`)的契约补全。

## 写接口与权限

POST/PUT/DELETE `moduleT/`,body:

```json
{"item": "moduleT" | "modulePropT" | "moduleNodeT", "parameter": { ... }}
```

- base 可改字段含四个算法槽位与 `startFun`、`name`、`describe` 等白名单项;
  prop/node 各有独立白名单。**修改(PUT)时出现白名单外字段,整个请求被 400
  拒绝**(「字段不在可修改范围内」);新建(POST)时多余字段被忽略不落库。
- 权限:系统模板要管理员;普通账号只能建个人模板(强制 `is_user=True`、
  classify=A、名称前缀受限)。改模板前先确认 list 接口返回的 `isOperator`。
- 修改模板属性/节点会直接影响参数注入契约,**改前必须与开发者确认**,并同步
  检查算法代码的形参是否需要联动修改。
