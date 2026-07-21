"""`domain.operation.Flash` 的公开调用契约。

此存根根据同目录 `Flash.py` 生成，供仅部署 `.pyd` 时的 IDE、静态检查和
业务 Skill 查询使用。它只覆盖业务模块可调用的公共 API；不声明双下划线
求根函数或 K 值迭代细节。

坐标和单位约定
----------------
* ``T`` 使用 K，``P`` 使用 Pa，``VF`` / ``GasRat`` 使用 0 到 1 的气相摩尔分率。
* ``F_mol`` 使用 kmol/s；``H_mol``、``HL_mol``、``HV_mol`` 使用 J/kmol；
  ``FH``、``FHL``、``FHV``、``target_duty``、``FHin`` 使用 J/s（W）。
* ``ZI``、``LXI_mol``、``VXI_mol``、``K`` 与所有 K 初值使用活跃组分局部坐标。
  当传入 ``SkipIndex`` 时，不能再向上述参数传入全组分向量。
* ``SkipIndex`` 是原全组分坐标下被过滤（通常为零组成）的索引；业务对外输出
  活跃组分向量时，应以 ``Comp_restore(values, Is0, Not0)`` 恢复全组分坐标。
* 常规 ``flash_*`` 求解器只支持单工况标量 T/P/VF；多工况物性计算应使用
  ``phy_prop`` / ``phy_propArray``，而不是向闪蒸接口传入数组。

返回约定
--------
* ``Instantiation=False`` 时，各闪蒸接口返回历史元组，顺序由类型别名说明。
* ``Instantiation=True`` 时，返回 ``FlashResults``；业务模块应优先用该结果回写
  ``T``、``P_in``、``GasRat``、相组成及 ``K``，避免遗漏字段或错用元组顺序。
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, overload

from domain.method.methodLV import MethodLV


Number = Union[int, float]
Vector = Sequence[Number]
SkipIndices = Optional[Sequence[int]]
FlashTuple = Tuple[float, Vector, Vector, Vector]
StateFlashTuple = Tuple[float, float, float, Vector, Vector, Vector]
BubbleTuple = Tuple[float, Vector, Vector]
LLETuple = Tuple[float, Vector, Vector, Vector]


def are_values_close(a: Any, b: Any, rtol: float = ..., atol: float = ...) -> bool: ...
def are_lists_close(list1: Sequence[Any], list2: Sequence[Any], rtol: float = ..., atol: float = ...) -> bool: ...
def convert_numpy_types(obj: Any) -> Any: ...
def Compare_SkipIndex_values(Input_variable: Any, Cache_variable: Any) -> bool: ...
def get_VF(VF: Number, K: Vector, ZI: Vector) -> float: ...
def save_cache(cache: Dict[str, Any], cache_file: str = ..., cache_updated: bool = ...,
               cache_data_true: bool = ...) -> None: ...
def print_output(output: Optional[Dict[str, Any]]) -> None: ...
def get_plt(X: Any, Y: Any, label: Any = ..., Type: Any = ..., title: str = ...,
            xlable: str = ..., ylable: str = ..., **kwargs: Any) -> Any: ...


class CalculateCacheData:
    """闪蒸缓存容器。

    该类用于历史闪蒸缓存的存取。新业务不应依赖缓存 key 的内部编码，只可通过
    ``update``、``get`` 和 ``get_`` 使用已存在的缓存上下文。
    """

    d: Dict[str, Any]

    def __init__(self) -> None: ...
    def update(self, d: Dict[str, Any]) -> None: ...
    def get(self) -> Dict[str, Any]: ...
    def get_(self, label: str, param: Sequence[Any]) -> Any: ...


class FlashResults:
    """`Instantiation=True` 时的闪蒸结果。

    常规 VLE 接口稳定设置 `T/P/VF/ZI/K/LXI_mol/VXI_mol/A/SkipIndex`。
    VLLE 结果可额外包含 `LLRat`、`GasRat`、`L_mol`、`L2_mol`、
    `L1XI_mol`、`L2XI_mol` 等字段。

    常规字段含义：
    * ``T`` / ``P``：求解后的状态温度/压力。
    * ``VF``：气相摩尔分率；``0`` 为全液相，``1`` 为全气相。
    * ``ZI``：活跃组分进料组成；``LXI_mol`` / ``VXI_mol``：对应相的活跃组成。
    * ``K``：气液平衡常数，满足近似 ``y_i = K_i * x_i``。
    * ``A``：非理想修正迭代量，仅用于诊断或初值相关历史逻辑，不应替代 ``K``。
    * ``SkipIndex``：与所有组分向量匹配的全局跳过索引。
    """

    T: float
    P: float
    VF: float
    ZI: Vector
    K: Vector
    A: Vector
    LXI_mol: Vector
    VXI_mol: Vector
    SkipIndex: SkipIndices
    LLRat: float
    GasRat: float
    L_mol: float
    L2_mol: float
    L1XI_mol: Vector
    L2XI_mol: Vector

    def __init__(self, **kwargs: Any) -> None: ...
    def __repr__(self) -> str: ...


class Flash(MethodLV):
    """单工况汽液闪蒸与能量计算基类。

    所有 `ZI`、相组成与 K 初值均使用活跃组分局部坐标。传入 `SkipIndex`
    时，它必须是原全组分坐标中的跳过索引。

    推荐业务调用顺序：
    1. 对全组分进料组成调用 ``Comp_filter``，得到 ``XI_mol_in, Is0, Not0``；
    2. 使用 ``XI_mol_in`` 和 ``SkipIndex=Is0`` 调用对应 ``flash_*``；
    3. 使用 ``FlashResults`` 回写状态、相组成和 K 值；
    4. 使用 ``get_H_LV_JB``、``get_F_LV_JB``、``get_H_F_LV_JB`` 计算能量；
    5. 对需要输出到外部 Flow 的组分向量调用 ``Comp_restore``。

    ``TP_BaseOn`` 等规格标志由 ``Input_type1`` 和 ``Input_type2`` 的中文输入
    类型组合计算，不根据 T/P/VF/duty 字段是否为 ``None`` 自动设置。
    """

    P_in: float
    GasRat: float
    LLRat: float
    XI_mol: Vector
    LXI_mol: Vector
    VXI_mol: Vector
    L2XI_mol: Vector
    F_mol: float
    FL_mol: float
    FV_mol: float
    FL2_mol: float
    H_mol: float
    HL_mol: float
    HV_mol: float
    HL2_mol: float
    FH: float
    FHL: float
    FHV: float
    FHL2: float
    K: Vector
    KLL: Vector
    T_Sat: Optional[float]
    T_Dew: Optional[float]
    K_Sat: Optional[Vector]
    K_Dew: Optional[Vector]
    DT: float
    DOA: float
    K_time: int
    feedback: Any

    def __init__(
        self,
        Data: Any = ...,
        Method_bag: Optional[str] = ...,
        DOA: float = ...,
        DT: float = ...,
        K_time: int = ...,
        *args: Any,
        **kwargs: Any
    ) -> None: ...

    # 继承自 MethodH 的物性入口；在 Flash 子类中作为稳定公共方法使用。
    # Property 为框架属性代码，T/P/V/XI/XI_mol 的单位和坐标以物性 Skill 为准。
    # T/P 或 XI 为多工况数组时 phy_prop 自动路由 phy_propArray；正式数组输入不广播。
    def phy_prop(self, Property: Optional[str] = ..., T: Any = ..., P: Any = ...,
                 V: Any = ..., XI: Any = ..., XI_mol: Any = ...,
                 SkipIndex: SkipIndices = ..., MixMode: int = ...,
                 *args: Any, **kwargs: Any) -> Any: ...
    def phy_propArray(self, Property: Optional[str] = ..., T: Any = ..., P: Any = ...,
                      V: Any = ..., XI: Any = ..., XI_mol: Any = ...,
                      SkipIndex: SkipIndices = ..., MixMode: int = ...,
                      *args: Any, **kwargs: Any) -> Any: ...

    # 常规 VLE 闪蒸。每组 overload 分别描述 Instantiation=False/True 的返回形态。
    # flash_TP: 已知温度、压力和进料组成，求气化率及气液相组成。
    @overload
    def flash_TP(
        self, T: Number = ..., P: Number = ..., ZI: Vector = ...,
        SkipIndex: SkipIndices = ..., VF0: Optional[float] = ...,
        K0: Optional[Vector] = ..., DewT: Optional[float] = ...,
        BubT: Optional[float] = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = False, *args: Any, **kwargs: Any
    ) -> FlashTuple: ...
    @overload
    def flash_TP(
        self, T: Number = ..., P: Number = ..., ZI: Vector = ...,
        SkipIndex: SkipIndices = ..., VF0: Optional[float] = ...,
        K0: Optional[Vector] = ..., DewT: Optional[float] = ...,
        BubT: Optional[float] = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = True, *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    # flash_TVF: 已知温度、气化率和进料组成，反求压力及气液相组成。
    @overload
    def flash_TVF(
        self, T: Number = ..., VF: Number = ..., ZI: Vector = ...,
        P0: Optional[float] = ..., K0: Optional[Vector] = ...,
        SkipIndex: SkipIndices = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = False, *args: Any, **kwargs: Any
    ) -> FlashTuple: ...
    @overload
    def flash_TVF(
        self, T: Number = ..., VF: Number = ..., ZI: Vector = ...,
        P0: Optional[float] = ..., K0: Optional[Vector] = ...,
        SkipIndex: SkipIndices = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = True, *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    # flash_PVF: 已知压力、气化率和进料组成，反求温度及气液相组成。
    @overload
    def flash_PVF(
        self, P: Number = ..., VF: Number = ..., ZI: Vector = ...,
        SkipIndex: SkipIndices = ..., T0: Optional[float] = ...,
        K0: Optional[Vector] = ..., DewT: Optional[float] = ...,
        BubT: Optional[float] = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = False, *args: Any, **kwargs: Any
    ) -> FlashTuple: ...
    @overload
    def flash_PVF(
        self, P: Number = ..., VF: Number = ..., ZI: Vector = ...,
        SkipIndex: SkipIndices = ..., T0: Optional[float] = ...,
        K0: Optional[Vector] = ..., DewT: Optional[float] = ...,
        BubT: Optional[float] = ..., iteration_factor: float = ...,
        iterative_method: str = ..., DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., Instantiation: bool = True, *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    # flash_TPVF: T/P/VF 恰好传入任意两个有效值，统一派发到 TP、TVF 或 PVF。
    # 业务优先直接使用语义明确的 flash_TP/flash_TVF/flash_PVF。
    @overload
    def flash_TPVF(
        self, T: Optional[Number] = ..., P: Optional[Number] = ...,
        VF: Optional[Number] = ..., ZI: Vector = ..., T0: float = ...,
        P0: float = ..., VF0: float = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., *args: Any, **kwargs: Any
    ) -> StateFlashTuple: ...
    @overload
    def flash_TPVF(
        self, T: Optional[Number] = ..., P: Optional[Number] = ...,
        VF: Optional[Number] = ..., ZI: Vector = ..., T0: float = ...,
        P0: float = ..., VF0: float = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    # 泡点与露点。BubT/BubP 返回平衡气相组成；DewT/DewP 返回平衡液相组成。
    # Instantiation=False 的 BubbleTuple 顺序固定为 (温度或压力, 相组成, K)。
    @overload
    def flash_BubT(
        self, P: Number, ZI: Vector, T0: Optional[float] = ...,
        K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., iteration_factor: float = ...,
        iterative_method: str = ..., *args: Any, **kwargs: Any
    ) -> BubbleTuple: ...
    @overload
    def flash_BubT(
        self, P: Number, ZI: Vector, T0: Optional[float] = ...,
        K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., iteration_factor: float = ...,
        iterative_method: str = ..., *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    @overload
    def flash_DewT(self, P: Number, ZI: Vector, T0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> BubbleTuple: ...
    @overload
    def flash_DewT(self, P: Number, ZI: Vector, T0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> FlashResults: ...

    def flash_SatT(self, P: Number, ZI: Vector, T0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = ..., DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> Any: ...

    @overload
    def flash_BubP(self, T: Number, ZI: Vector, P0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> BubbleTuple: ...
    @overload
    def flash_BubP(self, T: Number, ZI: Vector, P0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> FlashResults: ...

    @overload
    def flash_DewP(self, T: Number, ZI: Vector, P0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> BubbleTuple: ...
    @overload
    def flash_DewP(self, T: Number, ZI: Vector, P0: Optional[float] = ...,
                   K0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                   Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
                   K_time: int = ..., iteration_factor: float = ...,
                   iterative_method: str = ..., *args: Any, **kwargs: Any) -> FlashResults: ...

    # 焓/热负荷规格闪蒸。
    # flash_DP: 已知入口焓流、出口流量、目标热负荷、压力和组成，反求温度。
    # flash_DT: 已知入口焓流、出口流量、目标热负荷、温度和组成，反求压力。
    # FHin 为入口总焓流，target_duty 为相对入口的目标净热负荷；F_mol 不得为零。
    @overload
    def flash_DP(
        self, FHin: Number, F_mol: Number, target_duty: Number, P: Number,
        ZI: Vector, T0: Optional[float] = ..., K0: Optional[Vector] = ...,
        VF0: Optional[float] = ..., BubT: Optional[float] = ...,
        DewT: Optional[float] = ..., BubK: Optional[Vector] = ...,
        DewK: Optional[Vector] = ..., BubT0: Optional[float] = ...,
        DewT0: Optional[float] = ..., BubK0: Optional[Vector] = ...,
        DewK0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = False, HP_cal: bool = ..., DOA: float = ...,
        abs_DOA: float = ..., K_time: int = ..., *args: Any, **kwargs: Any
    ) -> StateFlashTuple: ...
    @overload
    def flash_DP(
        self, FHin: Number, F_mol: Number, target_duty: Number, P: Number,
        ZI: Vector, T0: Optional[float] = ..., K0: Optional[Vector] = ...,
        VF0: Optional[float] = ..., BubT: Optional[float] = ...,
        DewT: Optional[float] = ..., BubK: Optional[Vector] = ...,
        DewK: Optional[Vector] = ..., BubT0: Optional[float] = ...,
        DewT0: Optional[float] = ..., BubK0: Optional[Vector] = ...,
        DewK0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = True, HP_cal: bool = ..., DOA: float = ...,
        abs_DOA: float = ..., K_time: int = ..., *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    @overload
    def flash_DT(
        self, FHin: Number, F_mol: Number, T: Number, target_duty: Number,
        ZI: Vector, VF0: Optional[float] = ..., P0: Optional[float] = ...,
        K0: Optional[Vector] = ..., BubP: Optional[float] = ...,
        DewP: Optional[float] = ..., BubK: Optional[Vector] = ...,
        DewK: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = False, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., *args: Any, **kwargs: Any
    ) -> StateFlashTuple: ...
    @overload
    def flash_DT(
        self, FHin: Number, F_mol: Number, T: Number, target_duty: Number,
        ZI: Vector, VF0: Optional[float] = ..., P0: Optional[float] = ...,
        K0: Optional[Vector] = ..., BubP: Optional[float] = ...,
        DewP: Optional[float] = ..., BubK: Optional[Vector] = ...,
        DewK: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
        Instantiation: bool = True, DOA: float = ..., abs_DOA: float = ...,
        K_time: int = ..., *args: Any, **kwargs: Any
    ) -> FlashResults: ...

    def flash_HP(self, H_in: Number, H_diff: Number, P: Number, ZI: Vector,
                 T0: Optional[float] = ..., K0: Optional[Vector] = ...,
                 VF0: Optional[float] = ..., BubT: Optional[float] = ...,
                 DewT: Optional[float] = ..., BubK: Optional[Vector] = ...,
                 DewK: Optional[Vector] = ..., BubT0: Optional[float] = ...,
                 DewT0: Optional[float] = ..., BubK0: Optional[Vector] = ...,
                 DewK0: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                 Instantiation: bool = ..., DOA: float = ..., abs_DOA: float = ...,
                 K_time: int = ..., *args: Any, **kwargs: Any) -> Any: ...

    # 物料与能量辅助计算。
    # get_F_LV_JB 返回顺序为 (FV_mol, FL_mol)，与后续 get_H_F_LV_JB 参数顺序不同，
    # 调用时必须使用关键字或显式解包，避免将气液流量颠倒。
    def get_F_LV_JB(self, F_mol: Number, VF: Number) -> Tuple[float, float]: ...
    def get_F_XI_LV_JB(self, FV_mol: Number, FL_mol: Number,
                       VXI_mol: Vector, LXI_mol: Vector) -> Tuple[Vector, Vector]: ...
    def get_H_LV_JB(self, T: Number, P: Number, VF: Number,
                    LXI_mol: Vector, VXI_mol: Vector,
                    SkipIndex: SkipIndices = ...) -> Tuple[float, float, float]: ...
    def get_H_F_LV_JB(self, F_mol: Number, FL_mol: Number, FV_mol: Number,
                      H_mol: Number, HL_mol: Number, HV_mol: Number) -> Tuple[float, float, float]: ...
    def get_duty_by_flash(self, FHin: Number, F_mol: Number, T: Number,
                          P: Number, VF: Number, LXI_mol: Vector,
                          VXI_mol: Vector, SkipIndex: SkipIndices = ...) -> float: ...
    def get_duty_TVF(self, FHin: Number, F_mol: Number, T: Number, VF: Number,
                     ZI: Vector, SkipIndex: SkipIndices = ..., P0: Optional[float] = ...,
                     K0: Optional[Vector] = ..., DOA: float = ..., abs_DOA: float = ...,
                     K_time: int = ...) -> float: ...

    # 液液/汽液液平衡。
    # LLE/LLE_T 的 LLETuple 顺序为 (LLRat, L1XI_mol, L2XI_mol, KLL)。
    # VLLE 始终返回 FlashResults，但常规 VF 字段以 GasRat 字段表述三相结果。
    def LLE(self, T: Number, P: Number, ZI: Vector, key_comp: Any = ...,
            DT: Optional[float] = ..., DOA: Optional[float] = ...,
            K_time: Optional[int] = ..., SkipIndex: SkipIndices = ...,
            *args: Any, **kwargs: Any) -> LLETuple: ...
    def LLE_T(self, LLRat: Number, P: Number, ZI: Vector, DT: Optional[float] = ...,
              DOA: Optional[float] = ..., K_time: Optional[int] = ...,
              SkipIndex: SkipIndices = ..., *args: Any, **kwargs: Any) -> LLETuple: ...
    def VLLE(self, T: Number, P: Number, ZI: Vector, key_comp: Any = ...,
             SkipIndex: SkipIndices = ..., DT: Optional[float] = ...,
             iteration_factor: float = ..., iterative_method: str = ...,
             DOA: float = ..., K_time: Optional[int] = ...) -> FlashResults: ...
    def VLLE_PE(self, P: Number, GasRat: Number, ZI: Vector, key_comp: Any = ...,
                DT: Optional[float] = ..., DOA: Optional[float] = ...,
                K_time: Optional[int] = ..., *args: Any, **kwargs: Any) -> Any: ...

    # 流量换算。get_F_vol_mol 使用液/气摩尔密度及气化率将总体积流量换算为总摩尔流量。
    def get_F_vol_mol(self, F_vol: Number, DS_L: Number, DS_V: Number,
                      GasRat: Number) -> float: ...
    def Convert_to_moles(self, FReference: str, F_Input: Number, UnitType: str,
                         XI_Input: Vector, T: Number, P: Number) -> Tuple[float, Vector]: ...

    # 历史单元状态操作。它们直接读写 self 状态，主要保留给既有 Flow/operation 调用链。
    # 新业务优先使用前述无副作用的标准 flash_* 与 *_JB 接口，避免混合两套状态语义。
    def TP_BaseOn_Opration(self, T: Optional[Number] = ..., P_in: Optional[Number] = ...,
                            XI_mol: Optional[Vector] = ..., DT: Optional[float] = ...,
                            DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                            **kwargs: Any) -> float: ...
    def Te_BaseOn_Opration(self, T: Optional[Number] = ..., GasRat: Optional[Number] = ...,
                            XI_mol: Optional[Vector] = ..., DT: Optional[float] = ...,
                            DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                            **kwargs: Any) -> float: ...
    def Pe_BaseOn_Opration(self, P_in: Optional[Number] = ..., GasRat: Optional[Number] = ...,
                            XI_mol: Optional[Vector] = ..., DT: Optional[float] = ...,
                            DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                            **kwargs: Any) -> float: ...
    def get_T_Sat_Dew(self, P: Optional[Number] = ..., XI_mol: Optional[Vector] = ...,
                      T_Sat0: Optional[float] = ..., T_Dew0: Optional[float] = ...,
                      K_Sat0: Optional[Vector] = ..., K_Dew0: Optional[Vector] = ...,
                      DT: Optional[float] = ..., DOA: Optional[float] = ...,
                      K_time: Optional[int] = ..., *args: Any, **kwargs: Any) -> None: ...
    def get_sat_SC_N(self, P: Number, XI: Vector, T0: Optional[float] = ...,
                     K0: Optional[Vector] = ..., DT: Optional[float] = ...,
                     DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                     *args: Any, **kwargs: Any) -> BubbleTuple: ...
    def get_DewT_SC_N(self, P: Number, YI: Vector, T0: Optional[float] = ...,
                      K0: Optional[Vector] = ..., DT: Optional[float] = ...,
                      DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                      *args: Any, **kwargs: Any) -> BubbleTuple: ...
    def get_F_LV(self) -> None: ...
    def get_F_XI_LV(self) -> None: ...
    def get_H_mol_LV(self) -> None: ...
    def get_H_F_LV(self) -> None: ...
    def get_duty(self, FFin: Any) -> None: ...
    def get_duty_after_Opration(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                                 T: Optional[Number] = ..., P: Optional[Number] = ...,
                                 XI: Optional[Vector] = ..., **kwargs: Any) -> None: ...
    def get_duty_gas(self, GasRat: Number = ..., FFin: Any = ...,
                     F_mol: Optional[Number] = ...) -> None: ...
    def get_Q_BaseOn(self) -> Any: ...
    def get_Q(self, T_Dew: Number, T_Sat: Number, P: Number,
              XI_mol: Vector, H_mol: Number) -> Any: ...
    def Phase_check(self) -> Any: ...

    # 以下是源码保留的公开兼容接口。新业务应优先使用标准 flash_* 和 *_JB 方法。
    # simple 接口不进行完整非理想迭代；sovle_* 为历史拼写，不能按名称推断物理规格。
    def flash_BubT_simple(self, P: Number, ZI: Vector, A: Optional[Vector] = ...,
                          SkipIndex: SkipIndices = ..., T0: float = ...,
                          *args: Any, **kwargs: Any) -> BubbleTuple: ...
    def flash_DewT_simple(self, P: Number, ZI: Vector, T0: float = ...,
                          A: Optional[Vector] = ..., SkipIndex: SkipIndices = ...,
                          *args: Any, **kwargs: Any) -> BubbleTuple: ...
    def flash_TP_simple(self, T: Optional[Number] = ..., P: Optional[Number] = ...,
                        ZI: Optional[Vector] = ..., A: Optional[Vector] = ...,
                        SkipIndex: SkipIndices = ..., VF0: float = ...,
                        *args: Any, **kwargs: Any) -> FlashTuple: ...
    def flash_TVF_simple(self, T: Optional[Number] = ..., VF: Optional[Number] = ...,
                         ZI: Optional[Vector] = ..., A: Optional[Vector] = ...,
                         SkipIndex: SkipIndices = ..., P0: float = ...,
                         *args: Any, **kwargs: Any) -> FlashTuple: ...
    def flash_PVF_simple(self, P: Optional[Number] = ..., VF: Optional[Number] = ...,
                         ZI: Optional[Vector] = ..., A: Optional[Vector] = ...,
                         SkipIndex: SkipIndices = ..., T0: float = ...,
                         *args: Any, **kwargs: Any) -> FlashTuple: ...
    def flash_simple(self, T: Optional[Number] = ..., P: Optional[Number] = ...,
                     VF: Optional[Number] = ..., ZI: Optional[Vector] = ...,
                     A: Optional[Vector] = ..., T0: float = ..., P0: float = ...,
                     VF0: float = ..., SkipIndex: SkipIndices = ...,
                     Instantiation: bool = ..., DOA: float = ..., K_time: int = ...,
                     *args: Any, **kwargs: Any) -> Any: ...
    def DeltaTP_BaseOn_Opration(self, Tin: Optional[Number] = ..., K0: Optional[Vector] = ...,
                                GasRat0: Optional[Number] = ..., DOA: Optional[float] = ...,
                                K_time: Optional[int] = ..., *args: Any, **kwargs: Any) -> None: ...
    def OverColdP_BaseOn_Opration(self, K0: Optional[Vector] = ..., GasRat0: Optional[Number] = ...,
                                  DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                                  *args: Any, **kwargs: Any) -> None: ...
    def OverHotP_BaseOn_Opration(self, K0: Optional[Vector] = ..., GasRat0: Optional[Number] = ...,
                                 DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                                 *args: Any, **kwargs: Any) -> None: ...
    def DeltaTe_BaseOn_Opration(self, Tin: Optional[Number] = ..., K0: Optional[Vector] = ...,
                                P0: Optional[Number] = ..., DT: Optional[float] = ...,
                                DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                                *args: Any, **kwargs: Any) -> None: ...
    def TD_BaseOn_Opration(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                           GasRat0: Optional[Number] = ..., DT: Optional[float] = ...,
                           DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                           *args: Any, **kwargs: Any) -> None: ...
    def DeltaTD_BaseOn_Opration(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                                GasRat0: Optional[Number] = ..., DT: Optional[float] = ...,
                                DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                                *args: Any, **kwargs: Any) -> None: ...
    def PD_BaseOn_Opration(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                           T0: Optional[Number] = ..., DT: Optional[float] = ...,
                           DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                           *args: Any, **kwargs: Any) -> None: ...
    def sovle_DP(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                 T0: Optional[Number] = ..., DT: Optional[float] = ...,
                 DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                 *args: Any, **kwargs: Any) -> Any: ...
    def sovle_DT(self, FFin: Any = ..., F_mol: Optional[Number] = ...,
                 GasRat0: Optional[Number] = ..., DT: Optional[float] = ...,
                 DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                 *args: Any, **kwargs: Any) -> Any: ...
    def GetFai_l_LL(self, T: Number, P: Number, XI: Vector, Method_V: Any,
                    SkipIndex: SkipIndices = ..., **kwargs: Any) -> Vector: ...
    def get_K_value_N(self, T: Number, P: Number, XI: Vector, YI: Vector,
                      SkipIndex: SkipIndices = ...) -> Vector: ...
    def VLL_TP(self, T: Number, P: Number, ZI: Vector, key_comp: Any = ...) -> Any: ...
    def LLE_check(self, T: Number, xs: Vector) -> Any: ...
    def get_A(self, T: Number, P: Number, XI: Vector, YI: Vector,
              SkipIndex: SkipIndices = ..., Method_V: Any = ..., Method_L: Any = ...,
              where_used: str = ...) -> Vector: ...
    def iferrors(self, **kwargs: Any) -> Any: ...
    def get_GasRat_JB_2(self, T: Number, P: Number, ZI: Vector,
                         K0: Optional[Vector] = ..., GasRat0: Optional[Number] = ...,
                         DOA: Optional[float] = ..., K_time: Optional[int] = ...,
                         *args: Any, **kwargs: Any) -> Any: ...

    # 输入规格标识。它们由 Input_type1/Input_type2 的中文规格动态判断。
    # TP=温度+压力；Te=温度+汽化率；Pe=压力+汽化率；
    # DP=压力+热负荷；DT=温度+热负荷。
    @property
    def DTE_BaseOn(self) -> bool: ...
    @property
    def DTD_BaseOn(self) -> bool: ...
    @property
    def PDT_BaseOn(self) -> bool: ...
    @property
    def PDSH_BaseOn(self) -> bool: ...
    @property
    def PDSC_BaseOn(self) -> bool: ...
    @property
    def TP_BaseOn(self) -> bool: ...
    @property
    def Te_BaseOn(self) -> bool: ...
    @property
    def Pe_BaseOn(self) -> bool: ...
    @property
    def PP_BaseOn(self) -> bool: ...
    @property
    def DP_BaseOn(self) -> bool: ...
    @property
    def DT_BaseOn(self) -> bool: ...
    @property
    def D_Min(self) -> float: ...
    @property
    def D_Max(self) -> float: ...
