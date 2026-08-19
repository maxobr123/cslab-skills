# CSLab 通用数值边界保护

## 使用范围

本文适用于 `operation`、`dynamic`、`control`、`design`、`chemical-principle`、
`property-method` 及其他包含数值计算的 Python 算法。设备专用边界由所属族 Skill 补充，
但不得改变本文对数值保护、状态保留和回滚的统一约定。

数值保护处理正常运行中可恢复的越界、浮点扰动、局部计算失败和状态发布失败，不负责
修补模板字段缺失、接口不匹配、单位错误或未支持模型。后者仍按平台契约处理，不能通过
默认数值伪造成合法输入。

## 保护优先级

同一候选值不能直接采用时，按以下顺序选择保护方式：

1. 使用明确的物理边界关系恢复，例如容量约束、溢流或相分率端点。
2. 在开发者已确认容差内执行归零、归一化或边界投影。
3. 使用经过标量对比或回归测试验证的备用计算方法。
4. 使用上一有效值或上一已提交状态。
5. 没有安全候选值时不提交本次结果，保持原状态继续后续调度。

不得因为处理方便而无条件使用 `0`、`1`、机器 epsilon 或任意经验常数。保护值必须具有
明确的物理或数值含义。

## 技术方案保护表

编码前为实际涉及的量建立保护表；不适用项写“不适用”及理由。

| 项目 | 必须说明的内容 |
|---|---|
| 保护对象 | 变量、中间量、求解结果、矩阵 case、内部状态或出口对象 |
| 类型与单位 | 标量/数组、shape、组分坐标、物理单位和数据来源 |
| 合法边界 | 上下限、严格/非严格关系及边界等号的物理语义 |
| 容差 | `atol/rtol`、单位、依据和适用关系 |
| 保护动作 | 投影、归零、归一化、备用计算、上一有效值、跳过本步或回滚 |
| 守恒与状态 | 被修正量的守恒去向、旧状态保留范围和输出影响 |
| 验证工况 | 正常值、边界值、容差内外、局部失败和恢复后的预期结果 |

每个容差必须有独立名称，注明单位和适用关系。不得把同一个无量纲 epsilon 同时用于
温度、压力、流量、组成和守恒误差，也不得把机器精度直接当作物理容差。

## 统一返回约定

可复用的标量保护方法统一返回：

```python
protected_value, protection_applied
```

可复用的矩阵保护方法统一返回：

```python
protected_array, protection_mask
```

`protection_applied` 为布尔值；`protection_mask` 与被保护结果采用可明确定位失败 case 或
元素的形状。标记只用于测试、调试或统计，不作为业务错误返回，不改变平台入口契约。

状态推进不强制增加包装返回值。应在方法内部生成候选状态，只有候选状态完整可用且出口
发布成功时才提交；否则保持上一已提交状态。

## 九类通用保护层

| 保护层 | 使用场景 | 统一保护方式 |
|---|---|---|
| 有限值保护 | `NaN`、`Inf`、溢出结果 | 使用备用结果或上一有效值 |
| 上下限保护 | 温度、压力、流量、液位、汽化率 | 容差内投影；明显越界时保留旧值 |
| 非负保护 | 库存、流量、摩尔数、密度 | 小负值归零；大幅负值恢复旧值 |
| 组成保护 | 摩尔分数、质量分数 | 小负值归零后归一化；无法恢复时使用旧组成 |
| 数学定义域保护 | 除法、`log`、`sqrt`、`exp` | 使用已确认阈值、限幅、备用值或上一有效值 |
| 守恒保护 | 质量、摩尔、组分、能量、动量 | 按守恒关系重建状态或计算溢流、缺口 |
| 求解器保护 | 不收敛、无根、残差过大 | 缩小子步、备用求解器或上一有效解 |
| 状态提交保护 | 动态状态、缓存、Flow 出口 | 候选计算、快照、发布、提交；失败时回滚 |
| 矩阵局部保护 | 部分 case 或组分失败 | 只回退失败位置，正常 case 保留矩阵结果 |

## 通用方法示例

示例用于统一代码结构。已有项目公共方法能够满足相同语义时优先复用，不重复创建包装。

### 有限值保护

```python
def protect_finite(value, previous_value):
    """非有限候选值恢复为上一有效值，不抛异常。"""
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return previous_value, True

    if not np.isfinite(candidate):
        return previous_value, True
    return candidate, False
```

### 非负和范围保护

```python
def protect_nonnegative(value, previous_value, tolerance):
    """容差内的小负值归零，明显负值恢复上一有效值。"""
    value, protected = protect_finite(value, previous_value)
    if value is None:
        return None, True
    if value < -tolerance:
        return previous_value, True
    if value < 0.0:
        return 0.0, True
    return value, protected


def protect_range(value, lower, upper, previous_value, tolerance):
    """容差内投影到边界，明显越界时保留上一有效值。"""
    value, protected = protect_finite(value, previous_value)
    if value is None:
        return None, True
    if value < lower - tolerance or value > upper + tolerance:
        return previous_value, True
    projected = min(max(value, lower), upper)
    return projected, protected or projected != value
```

若变量没有上一有效值，不得擅自传入 `0` 作为 `previous_value`。初始化阶段应保持未初始化，
不发布候选结果，等待下一次获得完整有效输入。

### 组成保护

```python
def protect_composition(values, previous, component_count, tolerance):
    """恢复可修复组成；无法修复时使用上一有效组成。"""
    previous_copy = None if previous is None else np.asarray(previous).copy()
    try:
        composition = np.asarray(values, dtype=float)
    except (TypeError, ValueError):
        return previous_copy, True

    if (
        composition.ndim != 1
        or composition.size != component_count
        or not np.all(np.isfinite(composition))
        or np.any(composition < -tolerance)
    ):
        return previous_copy, True

    protected = bool(np.any(composition < 0.0))
    composition = np.maximum(composition, 0.0)
    total = float(np.sum(composition))
    if total <= tolerance:
        return previous_copy, True

    normalized = composition / total
    protected = protected or not np.isclose(
        total,
        1.0,
        atol=tolerance,
        rtol=0.0,
    )
    return normalized, protected
```

干设备、空相等已确认物理状态允许使用零组成时，应由调用方作为独立状态处理，不把零组成
传入需要归一组成的物性计算。

### 数学定义域保护

```python
def protected_divide(
    numerator,
    denominator,
    previous_value,
    denominator_limit,
):
    """分母过小或结果非有限时保留上一有效结果。"""
    try:
        numerator = float(numerator)
        denominator = float(denominator)
    except (TypeError, ValueError):
        return previous_value, True

    if not np.isfinite(numerator) or not np.isfinite(denominator):
        return previous_value, True
    if abs(denominator) <= denominator_limit:
        return previous_value, True

    result = numerator / denominator
    if not np.isfinite(result):
        return previous_value, True
    return result, False
```

`denominator_limit` 必须来自当前方程的尺度和精度要求。禁止统一使用
`denominator + 1.0e-12`，因为它会无条件改变所有正常结果。

`sqrt` 只允许把容差内的小负值投影到零；明显负值使用上一有效结果。`log` 的输入必须按
模型确认的正下限保护。`exp` 可按浮点范围限制指数，但必须说明限幅对物理结果的影响。

### 守恒边界投影

边界投影必须同步计算被截掉量的物理去向。容量保护示例：

```python
capacity_mass = density * area * height
if candidate_mass > capacity_mass:
    overflow_mass = candidate_mass - capacity_mass
    committed_mass = capacity_mass
    committed_level = height
else:
    overflow_mass = 0.0
    committed_mass = candidate_mass
    committed_level = committed_mass / (density * area)
```

不能只对液位执行 `clip` 而丢失超过容量的质量。不存在溢流、排放、回流或其他已确认去向
时，应保留上一已提交状态，而不是制造不守恒结果。

### 求解器保护

求解器必须保存上一有效解。新结果只有在有限、位于物理可行域且残差满足已确认容差时才
采用；否则依次尝试缩小子步或已验证备用求解器，仍不可用时继续使用上一有效解。

```python
try:
    candidate = solve_primary(initial_guess)
except Exception:
    candidate = None

candidate_valid = (
    candidate is not None
    and np.all(np.isfinite(candidate.value))
    and candidate.residual <= residual_tolerance
    and in_physical_domain(candidate.value)
)
if candidate_valid:
    protected_value = candidate.value
    protection_applied = False
else:
    try:
        fallback = solve_verified_fallback(initial_guess)
    except Exception:
        fallback = None
    if fallback is not None and fallback.is_valid:
        protected_value = fallback.value
    else:
        protected_value = previous_solution
    protection_applied = True
```

示例中的求解器对象名称是结构示意，不代表项目已有同名 API。实际实现应复用当前项目的
公开求解接口。

### 矩阵局部保护

矩阵路径使用掩码定位失败 case，只对失败范围调用已验证备用路径：

```python
try:
    candidate = calculate_array(...)
except Exception:
    candidate = np.full_like(previous, np.nan, dtype=float)
invalid_mask = ~np.isfinite(candidate)
protection_mask = invalid_mask.copy()

if np.any(invalid_mask):
    try:
        fallback = calculate_fallback_for_cases(invalid_mask)
    except Exception:
        fallback = np.full_like(candidate, np.nan, dtype=float)
    fallback_valid = np.isfinite(fallback)
    recovered = invalid_mask & fallback_valid
    unrecovered = invalid_mask & ~fallback_valid
    candidate[recovered] = fallback[recovered]
    candidate[unrecovered] = previous[unrecovered]
```

若属性输出 shape 为 `(case, component)`，测试和诊断应同时保留 case 与 component 索引。
不得因一个 case 失败而让整个矩阵回退旧循环，也不得用 `nan_to_num(..., nan=0)` 把失败
组分变成零贡献。

### 状态提交和出口回滚

外部对象可能在方法内部被部分修改，因此发布前必须建立快照：

```python
try:
    old_state = snapshot_internal_state()
    candidate_state = calculate_candidate(old_state, boundary)
    candidate_state, can_commit, protection_applied = protect_candidate(
        candidate_state,
        old_state,
    )
except Exception:
    return
if not can_commit:
    return

try:
    output_snapshot = snapshot_public_fields(output_flow)
except Exception:
    return

try:
    publish_output(output_flow, candidate_state)
    commit_internal_state(candidate_state)
except Exception:
    try:
        restore_public_fields(output_flow, output_snapshot)
    except Exception:
        pass
    try:
        restore_internal_state(old_state)
    except Exception:
        pass
    return
```

状态保护方法因多一个“是否可提交”的语义，统一返回
`(candidate_state, can_commit, protection_applied)`。示例中的 `except` 只恢复状态，不继续
抛出异常。出口发布或内部提交任一步骤失败时都尝试恢复出口快照和 `old_state`，避免槽内
状态和出口状态处于不同时间层级。

## Dtank 动态保护示例

| 场景 | 统一保护结果 |
|---|---|
| `Data.PGV["DT"]` 缺失、非有限或非正 | 当前步不推进，保留槽状态和出口状态 |
| 组成只有容差级负值 | 小负值归零后重新归一化 |
| 组成无法恢复 | 使用上一有效组成；没有上一值时保持未初始化 |
| 密度、热容或焓非有限 | 使用上一有效物性；没有有效历史值时不提交当前步 |
| 出口请求超过库存 | 限制为入口流量加单步可用库存 |
| 步内触满 | 定位首次触满时间并分段积分 |
| 超过设备容量 | 液位保持 `Height`，多余质量进入溢流 |
| RK4 候选状态失效 | 放弃候选状态，保持步初状态 |
| `flow_prop` 发布失败 | 恢复出口快照，槽状态不提交 |
| 干槽 | 库存和出口归零，保留最后有效温度和组成 |

## 禁止模式

以下写法缺少物理语义或状态保护，不得作为通用数值保护：

```python
# 所有异常都无条件变成零。
value = np.nan_to_num(value, nan=0.0, posinf=0.0, neginf=0.0)

# 没有说明被截掉质量或能量的去向。
level = np.clip(level, 0.0, height)

# 用任意 epsilon 改变全部正常计算结果。
result = numerator / (denominator + 1.0e-12)

# 发布失败后保留可能已经被部分修改的出口对象。
try:
    output.flow_prop(...)
except Exception:
    pass
```

`nan_to_num`、`maximum`、`clip` 本身不是禁止函数。只有零值或边界值具有明确物理意义、
守恒去向已经处理，并且保护表记录了该行为时才能使用。

## 验证检查单

每项实际使用的保护至少验证：

1. 正常值不触发保护，结果与未增加保护前一致。
2. 边界等号、容差内和容差外分别符合保护表。
3. `NaN`、正负 `Inf`、零分母和溢出不会进入已提交结果。
4. 组成保护后非负且归一；无法恢复时上一有效组成不变。
5. 投影后的质量、组分、能量或其他衡算仍闭合，被截掉量有明确去向。
6. 求解器主路径失败时只采用已验证备用解；备用路径也失败时保留旧解。
7. 动态候选状态失效时当前步不推进，上一状态和出口保持同一时间层级。
8. 出口发布中途失败后所有已确认公开字段恢复到快照值。
9. 矩阵局部失败只保护失败 case，正常 case 的数值和性能路径不受影响。
10. 所有数值保护分支均不抛异常、不发送错误反馈、不构造无消费者的失败返回。
