# Flash 相平衡公开接口

本文件是 TP、TVF、PVF、TPVF、泡点、露点和 LLE 业务接口的唯一事实源。
调用方统一使用关键字参数，不依赖默认值表达业务语义。单位、shape 和组分坐标见
[状态、坐标与失败契约](flash-state-contract.md)。

## 公共方法

下表中的“初值/控制”均为可选参数。常规 `flash_*` 还可通过
`Instantiation` 选择元组或结果对象返回。

| 方法 | 必需业务输入 | 常用初值/控制 | `Instantiation=False` 返回 |
|---|---|---|---|
| `flash_TP` | `T, P, ZI` | `SkipIndex, VF0, K0, DewT, BubT, iteration_factor, iterative_method, DOA, abs_DOA, K_time` | `VF, LXI_mol, VXI_mol, K` |
| `flash_TVF` | `T, VF, ZI` | `P0, K0, SkipIndex, iteration_factor, iterative_method, DOA, abs_DOA, K_time` | `P, LXI_mol, VXI_mol, K` |
| `flash_PVF` | `P, VF, ZI` | `T0, K0, DewT, BubT, SkipIndex, iteration_factor, iterative_method, DOA, abs_DOA, K_time` | `T, LXI_mol, VXI_mol, K` |
| `flash_TPVF` | `T/P/VF` 中恰好两项及 `ZI` | `T0, P0, VF0, SkipIndex, DOA, abs_DOA, K_time` | `T, P, VF, LXI_mol, VXI_mol, K` |
| `flash_BubT` / `flash_DewT` | `P, ZI` | `T0, K0, SkipIndex, DOA, abs_DOA, K_time` | `T, 另一相组成, K` |
| `flash_BubP` / `flash_DewP` | `T, ZI` | `P0, K0, SkipIndex, DOA, abs_DOA, K_time` | `P, 另一相组成, K` |
| `LLE` | `T, P, ZI` 及目标版本已验证的分层参数 | `SkipIndex, DOA, K_time` | `LLRat, L1XI_mol, L2XI_mol, KLL` |

设置 `Instantiation=True` 时，常规闪蒸返回结果对象；字段及校验方式以
[结果对象与返回模式](flash-state-contract.md#结果对象与返回模式)为准。不得混用元组顺序
和结果对象字段。

## 求解器选择

| 已知业务规格 | 调用 | 求解量 |
|---|---|---|
| `T + P + z` | `flash_TP` | `VF, x, y, K` |
| `T + VF + z` | `flash_TVF` | `P, x, y, K` |
| `P + VF + z` | `flash_PVF` | `T, x, y, K` |
| `P + FHin + duty + z` | [`flash_DP`](flash-duty-energy-api.md#热负荷闪蒸接口) | `T, VF, x, y, K` |
| `T + FHin + duty + z` | [`flash_DT`](flash-duty-energy-api.md#热负荷闪蒸接口) | `P, VF, x, y, K` |
| 定压泡点/露点 | `flash_BubT` / `flash_DewT` | 温度及另一相组成 |
| 定温泡点/露点 | `flash_BubP` / `flash_DewP` | 压力及另一相组成 |
| 液液分层 | `LLE` | 液液分率、两液相组成、`KLL` |

`TP_BaseOn`、`Te_BaseOn`、`Pe_BaseOn`、`DP_BaseOn`、`DT_BaseOn` 由
`Input_type1` 和 `Input_type2` 的中文规格组合判断：

| 标志 | 无序规格组合 |
|---|---|
| `TP_BaseOn` | `温度` + `压力` |
| `Te_BaseOn` | `温度` + `汽化率` |
| `Pe_BaseOn` | `压力` + `汽化率` |
| `DP_BaseOn` | `压力` + `热负荷` |
| `DT_BaseOn` | `温度` + `热负荷` |

不要根据字段是否为 `None` 自行设置这些标志。历史 `Flow.flashdp()` 和
`Flow.flashdt()` 的名称与其内部物理调用相反，新代码直接使用 `flash_DP` 和
`flash_DT`。

## 泡露点与 LLE

泡点返回平衡气相组成，露点返回平衡液相组成。元组模式统一为
`(状态值, 另一相组成, K)`。

`LLE` 元组为 `(LLRat, L1XI_mol, L2XI_mol, KLL)`。业务代码必须拒绝 `None`、
`LLRat <= 0`、`LLRat >= 1` 或两液相组成实质相同的伪分层结果。普通 VLE 不得改用
`LLE` 或 `VLLE`。

`flash_HP`、`flash_SatT`、`VLLE_PE` 和历史 `*_Opration`/`simple` 接口不属于本 Skill
推荐的新业务调用面。没有目标版本已验证的调用样例时，不生成这些接口的新代码。
