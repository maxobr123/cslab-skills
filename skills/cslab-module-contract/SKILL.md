---
name: cslab-module-contract
description: Use when writing any CSLab algorithm module regardless of family (steady operation, dynamic, control, design). Defines the platform-generic runtime contract - constructor injection, startFun, Run return convention, the three output channels, and feedback.
---

# 模块运行契约(平台通用,L2)

本 Skill 定义**所有模块族共享**的运行契约,由模板系统与调度框架决定,与具体
设备类型无关。族专有的变量词汇、继承方法、算法惯用法见对应族包
(稳态单元:`cslab-operation-skeleton`)。

## 参数注入契约(核心)

调度框架实例化模块的方式:按模板算法槽位 `importlib` 动态加载类,然后
`inspect.signature(类.__init__)` 取形参名集合,**同名注入**:

1. 模板属性 `name` 与形参**严格同名** → 作为关键字参数进构造函数;
   不同名 → 实例化后挂到 `instance.__dict__`(实例属性,构造函数里看不到)。
2. 节点(流股/能量流等)按**节点名 = 形参名**注入对象;类形参含 `Flow_list`
   时聚合注入 `[{"name": 流股实例, "nodeName", "position", "direction",
   "fraction", "Phase", "UnitType"}]`(仅聚合 FLOW 流股节点),
   `direction=="1"` 进、`"0"` 出。
3. **未连接的 FLOW/Energy 节点注入 `None`**,访问前必须判空。
4. `Data`(物性数据对象)、`pro`(项目 id)只要出现在形参里就由框架自动注入;
   `moduleName`/`moduleLabel`/`moduleID`/`startFun` 恒挂到实例。
5. **注入不做单位换算**:模板默认值与前端下发值直接进算法,算法内部一律按
   SI 计算,模板默认值必须已是 SI 数值。
6. 类型编码的特殊注入:组分系数类属性额外生成 `{属性名}_UnitType` 并转
   `np.array`;列表类转 `np.array`;引用赋值(多)类生成 `{属性名}__formula`。

因此 `__init__` 的铁律:形参名不是自由命名,是模板契约;末尾必须留 `**kwargs`
吞掉未声明的注入项;首行调用基类 `super().__init__(...)`,不要绕过。

## startFun 契约

框架按模板 `startFun`(稳态默认 `"Run"`,动态惯例 `Drun`/`DRun`)**无参**调用
`getattr(instance, startFun)()`:

- 入口方法除 `self` 外不得有无默认值参数。
- **方法名不存在时不报错**——框架按"成功、空结果"处理(静默假成功)。
  交付前必须核对模板 `startFun` 与方法名严格一致。

## 入口方法返回约定

返回二元组 `(计算状态, 结果字典)`:

- 成功:`return True, self.result`
- 失败:`return False, {}`(或模块定义的 `result_fail`,结构同 `result`、
  数值填零,用于空进料/不收敛)

`result` 为 `@property`,格式固定:

```python
{"result": {
    "出口温度": {"value": self.T, "unitType": "Temperature"},
    "汽化率": {"value": self.VF},          # 无量纲可省 unitType
}}
```

外层必须是 `{"result": {...}}`;键为面向用户的中文名;已知 `unitType` 枚举:
`Temperature`、`Pressure`、`Enthalpy flow`、`Mole flow`、`Mole enthalpy`。

## 三条输出通道(相互独立,缺一不可)

| 通道 | 机制 | 漏掉的后果 |
|---|---|---|
| `result` 字典 | 随返回值推送前端展示 | 用户界面看不到结果 |
| 同名实例属性 | 模板中输出属性(`is_input=否`),在入口方法里给**同名**实例属性赋值;框架计算后逐属性比对变更、按属性 id 回写数据库(仅回写:整数/浮点/字符串、种类为"普通"的列表、种类为"系数"的组分数组) | 结果不落库 |
| 写出口节点 | 把出口状态写回出口流股/能量流对象的字段 | 下游模块拿不到结果 |

## feedback 契约

- 签名 `self.feedback(label, msg, code=None)`;`label ∈ {"error","warn"}`,
  msg 中文;`error` = 无法继续,调用后走失败返回;`warn` = 提示不中断。
- 错误码 5 位:首 1-2 位为模块/领域段,后位为序号,同模块内同段递增。
  **错误码属平台约定,不得自造**:新告警没有对应码时先与开发者确认,
  或暂不带 `code` 只传文案。
- `feedback` 由调度框架在实例化后**动态注入**,模块不定义它。模块文件顶部放
  空桩 `def feedback_func(*args, **kwargs): pass`,本地测试时手动
  `instance.feedback = feedback_func`;类内直接调用 `self.feedback(...)`。
- 不用 `print` 上报信息,不用裸 `raise` 替代 feedback。

## 通用禁止事项

1. 形参名/入口方法名与模板不一致(注入与调用是纯名字匹配,错了不报错)。
2. 在模块内做单位换算或接收非 SI 输入。
3. 输出通道缺失(算对了但前端/库/下游拿不到)。
4. 未连接节点(`None`)不判空就访问。
5. 不依赖源码存在;不读取、修改、探测或反编译 `.so` 编译模块。
