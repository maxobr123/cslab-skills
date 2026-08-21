# CSLab 平台运行契约

本文是构造注入、入口调用、输出消费者和 `feedback` 的唯一详细定义。族 Skill 只引用，
不得复制后形成第二套口径。

## 构造与属性注入

调度框架按模板算法槽位导入类，通过 `inspect.signature(类.__init__)` 取得形参并同名注入：

1. 模板属性 `name` 与形参严格同名时作为关键字参数传入；不同名属性在构造完成后写入
   `instance.__dict__`，构造函数中不可读取。
2. FLOW/Energy 节点按节点名与形参名同名注入，未连接节点注入 `None`。
3. 类形参含 `Flow_list` 时，聚合注入 FLOW 节点字典列表，常见字段为 `name`、
   `nodeName`、`position`、`direction`、`fraction`、`Phase`、`UnitType`；
   `direction="1"` 为进，`"0"` 为出。
4. 形参包含 `Data` 或 `pro` 时由框架注入；`moduleName`、`moduleLabel`、`moduleID`、
   `startFun` 在构造后挂到实例。
5. 组分系数类属性可额外生成 `{属性名}_UnitType` 并转 `np.array`；列表类转数组；
   引用赋值（多）可生成 `{属性名}__formula`。具体类型以当前模板详情为准。
6. 注入不换算单位，模板默认值必须与算法使用的 SI 口径一致。

因此 `__init__` 形参是模板契约。只有当前模板、基类或公开调用方已经要求时才保留
`**kwargs`；不得以“未来扩展”为由添加，也不得用它绕过后台变量配置。当前调度器不会把
未声明模板属性送入 `**kwargs`。依赖构造后属性的状态在入口方法中延迟初始化。存在业务
基类时首行调用正确的 `super().__init__(...)`；无业务基类时不伪造继承链。

## startFun 与入口

平台基础控制器按模板 `startFun` 无参调用 `getattr(instance, startFun)()`：

- 普通入口除 `self` 外不得含无默认值参数。
- 方法名不存在时，部分控制器会按成功空结果继续，形成静默假成功；交付必须核对拼写。
- 动态 V4 的 `Run`、`RunDynamic`、`RunOde` 是族专用分派，读取
  `cslab-dynamic-module`，不要从通用规则猜测。

控制器版本或包装器改变时重新确认调用参数、返回消费者和错误传播。

## 返回与输出消费者

先读取实际控制器和族 Skill，再决定入口返回形式。基础控制器能接收二元组，也可能把
非二元组结果按成功处理；这不表示所有模块必须构造结果。

| 通道 | 必须实现的条件 | 发布机制 |
|---|---|---|
| 入口 `result` | 已核实前端或包装器消费入口返回 | 随入口返回面向用户的结果 |
| 同名实例属性 | 模板输出属性需要展示、落库或被引用 | 在本步集中更新同名属性 |
| 出口节点 | 下游模块或管网需要边界 | 写入 Flow、Energy 或其他节点对象 |

三种通道相互独立。没有消费者的通道不构造占位数据，也不能因为某通道不适用而漏掉其他
真实消费者。普通动态模块的实时输出通常依靠实例属性和出口节点，详见动态 Skill。

已确认需要稳态结果字典时，外层格式为：

```python
{"result": {
    "出口温度": {"value": self.T, "unitType": "Temperature"},
    "汽化率": {"value": self.VF},
}}
```

常见 `unitType` 包括 `Temperature`、`Pressure`、`Enthalpy flow`、`Mole flow`、
`Mole enthalpy`。中文键和具体枚举仍须以目标族及模板事实为准。

## feedback

- 调用签名：`self.feedback(label, msg, code=None)`；`label` 为 `error` 或 `warn`，
  `msg` 使用中文。
- `error` 表示当前计算无法继续，随后必须按所属控制器认可的方式结束；`warn` 不必中断。
- 错误码通常为 5 位，首 1–2 位属于模块/领域段，其余为同段递增序号。错误码属于平台
  约定，不得自造；缺少已确认错误码时先询问开发者，或只传文案。
- `feedback` 由框架在实例化后动态注入，业务类不定义它。
- 直接本地实例化时可在测试代码中挂空桩：

```python
def feedback_func(*args, **kwargs):
    pass

instance.feedback = feedback_func
```

不可继续的错误不能只返回一个控制器会忽略的状态。可恢复数值边界不使用错误反馈，按
`numerical-boundary-protection.md` 静默保护。

## 禁止事项

1. 模板形参、节点或入口名称不一致。
2. 假设框架会把非 SI 输入自动换算。
3. 未核实消费者就生成 `result`，或只写返回字典而漏掉出口和同名属性。
4. 未连接节点不判空。
5. 从 `.pyd/.so` 反推接口或实现；公开契约由 Skill references、模板和开发者证据提供。
