# Flash 状态、坐标与失败契约

本文件是 Flash 结果对象、单位、shape、组分坐标、校验回写、相边界和暖启动的唯一事实源。

## 继承与构造

```python
from domain.operation.Flash import Flash


class MyOperation(Flash):
    def __init__(
        self,
        Data=None,
        Method_bag=None,
        DT=0.01,
        DOA=0.005,
        K_time=100,
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

若目标类继承 `Flow`、`Utility_U` 等已有基类，沿用该类经过验证的构造契约，不为直接
继承 `Flash` 改变既有 MRO。

## 单位与组成坐标

变量含义和单位以
[operation 变量表](../../cslab-operation-unit-skeleton/references/operation-variables.md)
为唯一权威定义。

闪蒸始终使用活跃组分局部组成；对外写入 Flow 的组成必须恢复为完整项目组分坐标：

```python
self.XI_mol_in, self.Is0, self.Not0 = Comp_filter(
    np.asarray(full_xi_mol, dtype=float)
)

full_vapor_xi = Comp_restore(self.VXI_mol, self.Is0, self.Not0)
```

调用前检查 `ZI` 是一维、非负、和接近 1。传入非空 `SkipIndex` 时，不得同时传完整
长度组成；局部组成长度必须等于活跃组分数。不得在业务代码中再次切片 CAS、MW、
纯物性或二元参数。

## 结果对象与返回模式

- `Instantiation=False` 返回接口参考中声明的固定顺序元组。
- `Instantiation=True` 返回结果对象，适合完整回写业务状态。

常规结果对象的稳定字段为：

```text
T, P, VF, ZI, LXI_mol, VXI_mol, K, A, SkipIndex
```

不得把 `A` 当作 `K`。三相扩展字段只在对应三相接口实际返回时使用。

## 标准状态校验与回写

```python
result = self.flash_TP(
    T=self.T,
    P=self.P_in,
    ZI=self.XI_mol_in,
    SkipIndex=self.Is0,
    VF0=self.GasRat0,
    K0=self.K0,
    DOA=self.DOA,
    K_time=self.K_time,
    Instantiation=True,
)

required = ("T", "P", "VF", "ZI", "LXI_mol", "VXI_mol", "K", "SkipIndex")
if isinstance(result, str) or not all(hasattr(result, name) for name in required):
    raise RuntimeError(str(result))

vectors = [
    np.asarray(result.ZI, dtype=float),
    np.asarray(result.LXI_mol, dtype=float),
    np.asarray(result.VXI_mol, dtype=float),
    np.asarray(result.K, dtype=float),
]
try:
    values = np.asarray([result.T, result.P, result.VF], dtype=float)
except (TypeError, ValueError):
    raise RuntimeError("flash returned non-real T, P, or VF")
if values.shape != (3,) or not np.all(np.isfinite(values)):
    raise RuntimeError("flash returned an invalid state")
if values[0] <= 0.0 or values[1] <= 0.0 or not 0.0 <= values[2] <= 1.0:
    raise RuntimeError("flash returned nonphysical T, P, or VF")
if any(value.ndim != 1 or value.size != len(self.XI_mol_in) for value in vectors):
    raise RuntimeError("flash returned incompatible component coordinates")
if any(not np.all(np.isfinite(value)) for value in vectors):
    raise RuntimeError("flash returned non-finite component values")
if np.any(vectors[0] < 0.0) or not np.isclose(vectors[0].sum(), 1.0):
    raise RuntimeError("flash returned invalid feed composition")
if values[2] < 1.0 and (
    np.any(vectors[1] < 0.0) or not np.isclose(vectors[1].sum(), 1.0)
):
    raise RuntimeError("flash returned invalid liquid composition")
if values[2] > 0.0 and (
    np.any(vectors[2] < 0.0) or not np.isclose(vectors[2].sum(), 1.0)
):
    raise RuntimeError("flash returned invalid vapor composition")
if np.any(vectors[3] < 0.0):
    raise RuntimeError("flash returned invalid K values")
result_skip = [] if result.SkipIndex is None else list(result.SkipIndex)
expected_skip = [] if self.Is0 is None else list(self.Is0)
if result_skip != expected_skip:
    raise RuntimeError("flash changed SkipIndex unexpectedly")

# 全部校验通过后再发布新状态。
self.T = float(values[0])
self.P_in = float(values[1])
self.GasRat = float(values[2])
self.XI_mol_in = vectors[0]
self.LXI_mol = vectors[1]
self.VXI_mol = vectors[2]
self.K = vectors[3]
```

保留调用前生成且已校验相等的 `Is0/Not0`，不要用只有 `SkipIndex`、没有 `Not0` 的
结果对象替换其中一半坐标元数据。

`VF <= 0` 时不存在气相，`VF >= 1` 时不存在液相。下游端口是可复用对象时，必须清空
不存在相的旧状态，不能跳过写入而留下上次运行结果。

## 暖启动

同一方法包、同一 `SkipIndex`、相邻状态变化较小时，可以复用 `K0`、`VF0`、`T0`、
`P0` 和泡露点初值。以下任一情况必须丢弃旧初值：

1. `Method_bag` 或 `SkipIndex` 改变。
2. 活跃组分数或向量列坐标改变。
3. 状态或组成发生显著跳变。
4. 上一步不收敛、抛出异常或返回非有限值。

## Flash 专有失败规则

1. 调用前校验温度、压力、流量、组成和规格是否完整。
2. Flash 返回诊断字符串、非有限状态或不匹配的 shape/坐标时，视为失败。
3. 失败后清除暖启动值，不写入出口 Flow，不用 `np.nan_to_num` 伪造状态。
4. 不在业务层扫描温度或压力、实现有限差分求解，以替代公开 Flash 接口。
5. 异常记录和 `feedback` 使用 `cslab-module-contract` 的通用规则，本文件不重复定义。
