# FlashTank 构造、规格分派与暖启动

仅在目标已确认为 FlashTank 家族，且任务涉及构造器、MRO、模板输出初始化、输入规格或
暖启动时读取。变量含义和单位以
[`operation-variables.md`](../../cslab-operation-unit-skeleton/references/operation-variables.md)
为唯一事实源；Flash 方法签名以 `cslab-operation-flash` 为准。

## MRO 与构造器

下面只展示家族形态，不是可以直接套用的固定继承表。每个基类和参数都必须由目标模板或
同族 `.py` 证实：

```python
from domain.operation.Flow import Flow
from domain.operation.Public import Utility_U
from domain.baseClass.ReactionBase import ReactionBase
from domain.baseClass.Vessel import Vessel


class MyTank(Utility_U, Vessel, ReactionBase):
    def __init__(
        self,
        FFin: Flow,
        FDout: Flow,
        FWout: Flow,
        Input_type1=None,
        Input_value1=None,
        Input_type2=None,
        Input_value2=None,
        Method_bag=None,
        Data=None,
        mode=None,
        DT=0.01,
        DOA=1e-9,
        K_time=200,
        Utility=None,
        Height=None,
        Diameter=None,
        **kwargs
    ):
        super().__init__(
            Data=Data,
            Method_bag=Method_bag,
            DT=DT,
            DOA=DOA,
            K_time=K_time,
        )
```

构造参数通常先放注入 Flow，再放成对输入条件、Data/方法包、迭代参数和设备参数，最后
`**kwargs`；实际顺序必须服从模板实例化契约。多流股只在模板声明时使用 `Flow_list`。

Flash/物性能力、公用工程、容器和反应能力分别由目标真实基类提供，不能因为历史示例出现
`Utility_U/Vessel/ReactionBase` 就全部继承。Utility ID 到 `Data.PUW` 的解析也以当前基类
或同族实现为准，不在业务类重复硬编码。

## 模板输出属性初始化

模板中 `is_input=否` 且已确认由落库、前端或下游读取的属性，应在 `__init__` 以类型正确的
初值初始化；向量长度和坐标必须明确。属性严格同名，改大小写或拼写会造成字段丢失。

不要从历史 FlashTank 的长字段清单批量生成占位属性。`HHL/PW_out/Q/KA_Cont` 等只在当前
模板确实声明且消费者读取时存在；没有消费者的字段、结果和 helper 不创建。

## 输入条件与分派

已验证家族常用两对 `Input_type/Input_value` 表示温度、压力、汽化率或热负荷。映射关系必须
以当前基类/模板为准，典型语义为：

- 温度写入当前温度和输入记录。
- 正压力作为绝对压力；非正值可能表示相对上游的压差，必须先确认本族实现。
- 汽化率写入当前相分率。
- 热负荷写入本族实际使用的大小写字段。
- 连接 `DutyIn` 时，其 `Duty` 可能覆盖第二规格；只有目标模板证实才执行。

现有同族实现若保留 `set_duty()`，连接能量流时把第二输入条件切换为热负荷并读取
`DutyIn.Duty`；零值使用家族警告码 `30602`。没有能量流或目标模板采用其他规格注入方式时，
不得机械增加该方法。历史 `get_value()` 还会在未取得压力规格时发出“压力不是输入条件”的
无 code 警告；是否保留以目标同族控制器为准。

基类若已根据输入组合生成 `TP_BaseOn/Te_BaseOn/Pe_BaseOn/DP_BaseOn/DT_BaseOn`，`Run()`
直接按标志分派，不再写一套输入组合判断。典型对应关系如下：

| 标志 | 已知规格 | Flash 调用 | 后续计算 |
|---|---|---|---|
| `TP_BaseOn` | T、P | `flash_TP` | 按结果补算实际 duty |
| `Te_BaseOn` | T、VF | `flash_TVF` | 按结果补算实际 duty |
| `Pe_BaseOn` | P、VF | `flash_PVF` | 按结果补算实际 duty |
| `DP_BaseOn` | P、duty | `flash_DP` | 得到 T、VF |
| `DT_BaseOn` | T、duty | `flash_DT` | 得到 P、VF |

实际参数、返回字段和补算 helper 仍以 `cslab-operation-flash` 及同族契约为准。

现有 FlashTank 家族的输入失败码可作为同族证据核对：`30500` 表示入口无有效组分，
`30501` 表示入口无流量，`40500` 表示输入条件不足。新模块不能只因同属 operation 就复用；
先确认模板模块号段和控制器对 warn/error 的处理。

## 暖启动语义

典型暖启动记录包括上轮收敛的 T、P、VF、K、组成和 duty，但是否全部存在由目标族决定。

- 输入条件发生小幅变化时，可保留旧收敛值作为新工况迭代起点。
- 输入条件未变且组成未变时，才可直接复用对应 K 初值。
- 组成变化、方法包变化、活跃组分数或 `SkipIndex` 变化时，清空不兼容初值。
- 过滤 K 初值时必须同时得到新的跳过/保留索引，不能只改一半坐标。
- 初值的有限性、温压范围、汽化率范围或向量长度不合格时直接丢弃。

目标同族确有以下生命周期方法时，保持其字段集合和调用方向：

- `init_starter()` 清空 `P0/T0/K0/VF0/XI0/duty0`。
- `set_value()` 成功提交前后按既有调用链保存本轮收敛的 K、VF、P、T、组成和 duty，供下轮
  使用；不要在失败路径保存。
- 为兼容继承 Flash 的字段契约，需要时同步 `self.P = self.P_in`，但不能把这一别名扩散为
  所有 operation 单元的固定字段。

不要把“输入条件变化就清空全部初值”写成固定规则；流程迭代中小幅变化正是暖启动的主要
使用场景。也不能在坐标变化后为了收敛速度强行保留 K。

## Run 控制流提示

```python
def Run(self):
    # 第 1 步：同步已确认的能量流规格并校验入口。
    self.set_duty_if_configured()
    self.validate_feed_and_specifications()

    # 第 2 步：判断暖启动，随后过滤完整组成。
    self.prepare_warm_start()
    self.XI_mol, self._Is0, self.Not0 = Comp_filter(
        np.asarray(self.FFin.XI_mol, dtype=float)
    )

    # 第 3 步：按基类已经生成的分派标志调用 Flash，并校验完整结果。
    self.Flash_core = self.run_confirmed_flash_specification()
    self.publish_flash_state_locally()

    # 第 4 步：完成相流量、能量、容器及已启用扩展计算。
    self.calculate_confirmed_derived_state()

    # 第 5 步：恢复完整坐标，全部成功后提交外部消费者。
    self.restore_full_coordinates()
    self.commit_consumed_outputs()
    return self.build_consumed_return()
```

该代码只表示阶段，不要求创建这些 helper。简单模块可在 `Run()` 内完成；不得为了模板外观
增加无消费者、无复用价值的空方法。
