---
name: cslab-modulet-api
description: Use when querying or modifying CSLab module templates over HTTP - direct account login and token refresh, device type categories, template list and detail, backend configuration and API verification of new module contract variables, API-derived variable catalog maintenance, pyTemp skeleton generation, template CRUD, and template-to-algorithm mapping fields.
---

# moduleT 模板接口契约

模板系统是"模块参数的唯一事实来源":一个模板(moduleT)定义了模块的基础信息、
参数属性(moduleProp)、连接节点(moduleNode),以及指向 `domain/` 下对应算法目录的
类路径。开发模板驱动算法前先通过这些接口取模板,推导构造契约。

## 地址与鉴权

- 基础前缀:`${CSLAB_SERVER_HOST}/cslab-server/`(变量名以实际 ENV 注入为准)。
- `moduleT/` 系列需要 JWT:请求头 `Authorization: JWT ${CSLAB_TOKEN}`
  (服务端取空格后第二段,前缀词不敏感)。
- 响应统一包装:`{"status": 200, "msg": "成功", "data": <业务数据>}`,先判
  `status` 再取 `data`。

### 后台访问触发与凭据门禁

- 仅在开发者要求读取/修改后台模板,或开发任务必须核对当前模板注入契约、验证新增
  变量是否已配置时访问后台。普通代码阅读、算法开发和已有目录查询不得预先索取凭据。
- 每个新的已认证后台访问任务中,如果开发者没有在当前任务明确提供账号密码或有效的
  短期令牌,先说明服务器地址、访问目的和只读/写入范围,再请开发者提供账号和密码。
  已在当前任务明确提供的凭据不重复询问。
- 账号密码授权只允许登录,不等于授权新增、修改或删除模板。写接口仍必须单独完成业务
  方案确认、目标模板确认、完整 payload 确认和写入授权。
- 账号、密码、`token`、`rtoken` 仅在当前任务的进程内存中使用。禁止写入 Skill、源码、
  配置、临时文件、Shell 历史、日志或 Git,也禁止在命令输出和最终答复中展示实际值。
- 不从浏览器 localStorage/cookie、历史文件、日志或 Git 中搜集凭据。没有安全输入通道时,
  停止登录并说明限制,不得把密码拼进会持久化的脚本或调试文件。

### 无 UI 账号登录

获取后台模板时默认直接使用 HTTP,没有必要不得打开网页 UI:

1. `GET auth/image/`,确认 `status=200`,从 `data` 取 `key`、`x`、`y`。
2. `POST login/`,JSON body 使用:
   `username`、`password`、`key`、`image_verify_code: [x, y]`、`device_type`。
3. 确认登录包装响应 `status=200`,仅在内存中保存 `data.token` 和 `data.rtoken`；只允许
   输出“是否取得令牌”,不得输出令牌正文或完整登录响应。
4. 普通 API 请求使用 `Authorization: jwt <token>` 和 `DEVICE-TYPE: <device_type>`。

当前部署的 `auth/image/` 会返回可按正式接口契约提交的验证参数。若其他部署要求开发者
人工完成验证码、MFA 或 SSO,停止自动登录并请开发者处理,不得破解或绕过安全验证。仅在
HTTP 契约不可用、必须人工认证或开发者明确要求观察网页操作时使用 UI。

### 令牌刷新与并发控制

- token 有效期很短(服务端 `JWT_EXPIRATION_DELTA` 配置,当前部署实测约 900 秒)。登录站
  当前在首次登录后把刷新检查点设为 `Date.now() + 780 * 1000`,以便提前刷新。
- 不持续轮询。每次发送已认证请求前检查刷新时间;长时间无请求时不产生额外流量。
- 到达刷新检查点后调用 `GET auth/refresh/`,请求头使用
  `Authorization: jwt <rtoken>` 和 `DEVICE-TYPE`。注意此处使用刷新令牌,不是旧 token。
- 刷新成功且包装响应 `status=200` 后,原子替换 `data.token`、`data.rtoken` 和下一刷新
  时间。当前前端以 HTTP `Date` 响应头校正 `data.timestamp` 到本地时钟。
- 并发请求必须采用 single-flight:同一时刻只发一个刷新请求,其他请求等待该结果后再
  读取新 token,不得并发重复刷新或继续使用已经被替换的 rtoken。
- 刷新网络失败、业务失败、401,或业务接口返回
  `{"status": "40001", "msg": "签名已过期", "state": "40001"}` 时,清除内存中的
  token、rtoken 和刷新时间。`40001` 的 `status` 可能是字符串,判断时兼容字符串/数字。
  仍持有本次任务凭据时最多重新登录一次;再次失败则停止并报告,不得无限重试或伪造数据。

## 接口总表

| 接口 | 方法 | 用途 |
|---|---|---|
| `moduleT/deviceType/` | GET | 设备类型分类字典 |
| `moduleT/list/` | GET | 模板列表(查询参 `module_type`、`isUser`) |
| `moduleT/?pk=<id>` | GET | 单模板详情:module/moduleProp/moduleNode |
| `moduleT/pyTemp?pk=<id>&class_name=<类名>` | GET | 由模板生成 Python 类骨架 |
| `moduleT/` | POST/PUT/DELETE | 模板/属性/节点增改删,body `{"item":..., "parameter": {...}}` |

## 无 UI 模板查询流程

1. 按“后台访问触发与凭据门禁”确认确有后台查询需要,再通过无 UI 登录取得短期令牌。
2. 调用 `moduleT/list/` 获取候选,按 `name`、`label`、中文描述和目标算法名匹配。多个
   候选时完整展示给开发者选择,不得自行猜测。
3. 选定模板后只调用一次 `moduleT/?pk=<id>`。该详情 GET 存在归一化回写副作用,不得因
   输出格式或调试需要反复请求;应在内存中完成字段压缩和多种视图整理。
4. 核对 `startFun` 和四个算法槽位,确认目标文件与类名,例如
   `dynamic.Dtank_Opensgy,Dtank_Open`。
5. 整理 `moduleProp`、`moduleProp7`、`moduleNode`;对 `{describe, value}` 包装字段提取
   当前值。下拉字段的 `value=[当前值, 全部候选]`,不要把候选全集误报为模板参数。
6. 属性至少报告变量名、中文含义、类型、默认值、输入/输出、单位、冷态和计算状态;
   节点至少报告名称、含义、节点类型、方向和相态。单位为空、名称疑似错误等只标记为
   “后台当前配置/待确认”,不得自行修正后冒充 API 事实。
7. 输出登录状态、模板 ID、算法映射和整理后的契约即可。禁止输出完整鉴权响应、实际
   Authorization 请求头、带令牌 URL 或任何账号密码/token/rtoken。
8. 将新取得且已由详情 API 证实的变量与后台变量目录比对并补充;当前模板的实际契约仍
   以本次详情响应为准。

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

1. `<目录>.<文件名>` —— 类名 = 点分末段，例如 `operation.FlashTank`、
   `dynamic.Dtank_Open`；
2. `<目录>.<文件名>;<类名>` —— 类名与文件名不同时(分隔符 `; ； , ， |` 均可);
3. `.py/.pyd/.so` 绝对路径。

scheduler 按 `importlib.import_module("domain." + 路径)` 加载,再 `getattr` 取类。

## 项目实例数据与本地算法边界

`moduleT` 是模板定义事实源；具体项目中的实际属性值、节点连接和执行顺序来自
`POST obtainData/CalculateData/`。项目联调可通过
`HttpLoadData(host).load_module_data(payload)` 获取，其中 payload 至少含 `pro` 和
`callow_item`，并按运行入口补充 `canvas/pk/special_pk/is_custom_sequence/`
`is_only_checked/need_converge`。

项目数据只来自服务器，本地工程运行入口仍通过模板槽位导入本地 `domain/.../*.py` 或
依赖二进制。入口路径不是平台固定契约，先在当前项目检索并确认，不能假定存在某个
`moduleRunBase.py`。网页服务器上的算法文件不会自动替代本地文件，也不能用网页运行结果
证明本地源码已加载。`CalculateData` 缺少的 `is_input` 等模板语义仍以 `moduleT` 详情为准，
不根据实例值猜测输入/输出方向。

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

## 新增模块契约变量配置

开发算法需要新增且当前模板详情、项目 Skill 和后台模板变量目录均未约定的模块契约
变量时，必须先形成“待配置后台变量清单”，由开发人员确认并在后台完成配置。模块契约
变量包括构造函数注入参数、模板输入/输出、需落库或前端展示的实例属性、可配置状态、
初始条件、边界条件和连接节点；方法局部量、中间计算量、循环变量及私有缓存不属于
后台配置范围。

### moduleProp 配置建议字段

| 字段 | 必须说明的内容 |
|---|---|
| `name` | Python 英文变量名，并说明与构造形参或实例属性的同名关系 |
| `describe` / `desc` | 中文简称、完整业务含义与用途 |
| `classify` / `classify2` | 数据类型及复合元素类型 |
| `value` | 默认值及 SI 口径；没有合理默认值时明确要求后台补齐 |
| `unitType` / `unit` / `opt_unit` | 物理量类型、存储单位和可选展示单位 |
| 数据形状 | 标量、向量或矩阵，以及组分坐标和维度规则 |
| 有效范围 | 最小值、最大值、枚举集合或其他约束 |
| `is_input` | 输入或输出语义，以及构造注入或落库方式 |
| 数据来源 | 开发人员输入、上游模块、状态量、方程求解或其他明确来源 |
| 输出消费者 | 入口返回、`result`、同名实例属性、出口对象或其他调用方；没有消费者的通道标记不适用 |
| 模板范围 | 目标 `t_module_pk`、模板名和设备族；禁止默认提升为公共变量 |
| `source` / `relyOn` / `relyOn7` / `hide` | 枚举源、联动和显示条件；不适用时明确写无 |
| 状态规则 | `cold_state`、`calculate_state_judgement` 及计算前后保存规则 |

### moduleNode 配置建议字段

除变量名、中文含义、模板范围外，节点清单还必须说明 `code`、`interface`、`phase`、
是否允许未连接、对应的 Python 注入形参和上下游语义。不得只给出节点英文名。

### 配置与 API 复核流程

1. 先读取当前 `GET moduleT/?pk=<t_module_pk>`、项目 Skill 和后台变量目录，确认变量
   确实未配置，避免重复创建或误改同名变量。
2. 将上述完整配置建议纳入技术方案。开发人员必须先理解并确认技术方案，再决定自行
   配置或明确授权 Agent 写入。权限授权本身不等于业务方案确认。
3. Agent 代写时，必须已获得目标模板、完整 POST/PUT payload 和写权限的明确授权；
   不得从变量名推测缺失字段，不得修改未授权模板。
4. 配置完成后重新调用 `GET moduleT/?pk=<t_module_pk>`，逐字段核对名称、类型、单位、
   默认值、方向、形状和节点契约。列表摘要、截图中的局部字段或写接口成功响应不能替代
   详情 API 复核。
5. 只有详情 API 复核通过后，才能将该变量加入“已确认后台属性/节点”目录并用于编码；
   否则保留在当前方案的待配置清单，停止算法实现。

禁止用 `**kwargs`、硬编码默认值、运行时临时属性或未登记节点绕过后台模板契约。

## 后台模板变量目录

查询模板详情或由开发者提供后台配置证据时，读取并持续更新
[`references/backend-template-variables.md`](references/backend-template-variables.md)。
目录保存后台已确认的变量名、简称、描述、单位、方向、模板范围和来源状态，供后续开发
参考；当前模板的实际注入契约仍以本次详情响应为准。

每次成功取得新的 `moduleProp` / `moduleNode` 后，都要在当前任务内完成目录比对：
新增未收录项、补齐待补字段、按模板保留同名冲突，并纠正已被 API 证据推翻的旧推测。
不得只在对话中展示而不沉淀，也不得把列表接口摘要或 Agent 推断当作模板详情事实。

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
(整数/浮点形参带 `int`/`float` 类型标注;**默认值一律渲染为 `=None`**,模板里的
默认值不会出现在骨架里)。局限:**无 `Data`/`Method_bag` 形参、无基类继承、
`Run` 为空桩**,只能当起点,必须按 `cslab-module-contract` 与所属族包
(通用稳态单元使用 `cslab-operation-unit-skeleton`，FlashTank 另加
`cslab-operation-flashtank`，动态模块使用 `cslab-dynamic-module`)的契约补全。

**已知 500 陷阱**:服务端对 classify=0/1 的属性无防御地执行 `int(value)` /
`float(value)`。模板中任一数值属性默认值为 NULL(属性类型切换会把 value 置空,
库中常见)时,接口返回 500「服务器内部错误: float() argument must be a string
or a number, not 'NoneType'」(整数属性则是 int() 版本)。这是模板脏数据触发的
服务端缺陷,不是调用方式问题,重试无用。**兜底**:改走 `moduleT/?pk=<id>` 模板
详情,按 moduleProp 的 `name`/`classify` 与 moduleNode 的 `name` 手工拼骨架——
pyTemp 本就不渲染默认值,兜底不损失信息;同时把详情中 classify=0/1 且 value 为
空的属性名报给开发者,在模板里补上默认值后 pyTemp 即恢复。

其他坑:`class_name` 缺省或非法标识符不报错,渲染出 `class None:` 之类非法代码;
`pk` 不存在返回 200 的空壳骨架而非 404;prop 名与 node 名重名会生成重复形参。
拿到骨架先过一遍语法检查(如 `ast.parse`)再用。

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
