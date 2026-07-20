---
name: cslab-module-develop
description: Use as the entry-point workflow when developing, modifying, or debugging a CSLab domain/operation algorithm module. Covers requirement clarification, locating the module template via moduleT API, deriving the constructor contract, writing the algorithm, local verification, and delivery.
---

# CSLab 业务模块开发工作流

本 Skill 是开发 `domain/operation/` 业务算法模块的**总入口**。收到"写/改某个模块算法"
的需求时,从这里开始,按步骤推进,并在对应步骤加载配套 Skill:

| 层 | 配套 Skill | 何时加载 |
|---|---|---|
| L2 | `cslab-modulet-api` | 步骤 2、3、6:查模板分类/列表/属性,生成骨架,改模板 |
| L2 | `cslab-module-contract` | 步骤 4:平台通用运行契约(注入、startFun、输出通道、feedback) |
| L2 | `cslab-module-verify` | 步骤 5:本地验证与调试 |
| L3 | 模块族包 | 步骤 4:按目标模块所属族加载(见下表) |

模块族包路由(按模板算法槽位/设备类型判断所属族):

| 族 | 族包 Skill | 状态 |
|---|---|---|
| 稳态单元(`domain/operation/`) | `cslab-operation-skeleton` + `cslab-operation-flash` + `cslab-operation-phy-prop` | 可用 |
| 动态 / 控制 / 设计 / 化原 等 | 待建 | 无族包时明确告知开发者该族契约尚未沉淀,不要套用稳态族词汇硬写 |

## 环境准备

运行环境会注入以下变量(变量名以实际注入为准,若环境已有同义变量优先使用):

- `CSLAB_SERVER_HOST`:服务端地址,接口统一前缀为 `${CSLAB_SERVER_HOST}/cslab-server/`
- `CSLAB_TOKEN`:JWT,`moduleT` 系列接口必需,请求头 `Authorization: JWT ${CSLAB_TOKEN}`

`obtainData/`、`storeData/` 取数接口无需鉴权。任何接口不可达或 401 时,先向开发者
确认 ENV 是否注入,不要凭记忆猜地址或伪造数据。

## 步骤 1:厘清需求

先弄清开发者真正要什么,再动手。逐项确认(已明确的跳过,一次只问最关键的缺口):

1. **改还是新建**:是修改现有模板的算法,还是新设备/新模板?给出模板名或大致设备类型。
2. **计算模式**:稳态 / 动态 / 化工原理 / 设计,对应模板的 `steady_module` /
   `dynamic_module` / `chemical_principle_module` / `design_module` 四个算法槽位之一。
3. **输入条件组合**:哪些量是用户输入(如 T/P、P/汽化率、P/热负荷),哪些是算出来的?
   这决定算法内部走哪条闪蒸/求解分支。
4. **进出流股**:几进几出?各是什么相态?是否有能量流(DutyIn)?
5. **期望输出**:前端要展示哪些结果(`result` 字典)?哪些要作为模板属性落库?
6. **附加机制**:是否涉及反应(RList)、公用工程(Utility)、动态罐体参数?

需求含糊时先复述一遍你的理解让开发者确认,再进入下一步。

## 步骤 2:定位模板

加载 `cslab-modulet-api`,按序调用:

1. `GET moduleT/deviceType/` → 拿设备类型分类,和开发者对齐是哪一类。
2. `GET moduleT/list/` → 在列表中按 `name`/`label`/`describe` 匹配候选模板;
   有歧义时把候选列给开发者选。
3. `GET moduleT/?pk=<t_module_pk>` → 拉全量模板属性(`module` / `moduleProp` /
   `moduleNode`),这是后续所有推导的事实来源。

改现有算法时,`module` 里对应算法槽位的值(如 `operation.FlashTank`)就是要改的
文件与类;新建模板时该槽位由步骤 6 回填。

## 步骤 3:推导构造契约

框架用 `inspect.signature(类.__init__)` 做**同名注入**,所以模板属性/节点与代码的
对应关系是硬契约,必须先推导再写代码:

1. 遍历 `moduleProp`:每个属性的 `name`(英文变量名)即候选形参名;`is_input=是`
   的是输入参数,`is_input=否` 的是输出属性(不进构造函数,但 `Run()` 里要给同名
   实例属性赋值才能落库)。记录每个输入的类型编码(`classify`)、默认值、单位——
   **注入时不做单位换算,默认值必须已是算法期望单位(SI)**。
2. 遍历 `moduleNode`:流股/能量节点的 `name` 即构造函数的流股形参名(如 `FFin`、
   `FDout`);`interface` 区分进出。多流股模块用 `Flow_list` 聚合形参。
   未连接的节点会注入 `None`,算法必须容忍。
3. 记下 `startFun`(默认 `Run`)——类里必须有严格同名方法;拼错不会报错,
   框架按"成功、空结果"处理,属于静默假失败。
4. 输出一张"模板属性 ↔ 形参/实例属性"对照表,作为写代码的检查基准。

## 步骤 4:编写算法

1. 起点可用平台骨架:`GET moduleT/pyTemp?pk=<id>&class_name=<类名>`。
   注意骨架只有形参与空 `Run`,**缺 `Data`/`Method_bag` 形参、缺基类继承**,
   必须按契约补全。
2. 加载 `cslab-module-contract` 落实平台通用契约:注入、startFun、返回约定、
   三条输出通道、feedback。
3. 加载所属**族包**写类结构与算法体(稳态单元:`cslab-operation-skeleton`,
   闪蒸用 `cslab-operation-flash`,物性用 `cslab-operation-phy-prop`)。
4. 全程遵守通用契约与族包的禁止事项(不反编译 `.so`、不混用组分坐标系、
   不把多工况数组传给 `flash_*`)。

## 步骤 5:本地验证

加载 `cslab-module-verify`:写 `__main__` 脚手架(`obtainData` 免鉴权取数 → 建
`Data`/`Flow` → 建模块 → `Run()` → 检查 `result`),按其检查单核对返回值形态、
落库属性、出口流股回写。注意 `.so` 是 Linux/Python3.7 二进制,验证必须在对应
环境执行,macOS 本机只能做静态审查。

## 步骤 6:交付与登记

1. **算法文件**:交付 `.py`,说明落点为服务器根 `domain/operation/`(scheduler 经
   符号链接加载,无需编译;**没有上传 API**,落文件走部署渠道)。
2. **模板回填**(新建或换文件时):用 `cslab-modulet-api` 的写接口把算法槽位设为
   `operation.<文件名>`(类名与文件名不同时用 `operation.<文件名>;<类名>`),
   核对 `startFun`。注意权限:系统模板需管理员,普通账号只能建个人 A 类模板。
3. **交付说明**:向开发者汇总——改了哪些文件、模板哪些字段需要/已经变更、
   验证结论(跑通/未跑通及原因)、遗留风险。

## 红线速查

1. 模板属性名/节点名与形参名**必须严格同名**,这是唯一的参数注入通道。
2. `startFun` 拼错 = 静默假成功,交付前必须核对。
3. 属性注入不做单位换算,所有默认值与算法内部计算一律 SI 单位。
4. 前端展示走 `result`,落库走同名实例属性赋值,出口状态走写出口流股——三条通道
   相互独立,漏一条就是"算对了但看不到"。
5. 未连接节点注入 `None`,访问前判空。
6. 接口取不到的信息(模板字段、物性行为)直接问开发者或查代码,不要编造。
