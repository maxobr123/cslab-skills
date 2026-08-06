# CSLab 热力学与数学公共常量

本表是 operation 物性和闪蒸代码选择公共常量引用路径的权威来源。优先引用项目主常量
模块，不在业务算法中重复写数值。`PI` 不是项目导出名，圆周率使用小写 `pi`。

## 项目热力学主常量

推荐引用：`thermo_supports.math_untils.thermodynamic_constant`。

| 名称 | 含义 | 数值/表达式 | 单位 | 引用路径 |
|---|---|---|---|---|
| `T_init` | 热力学积分基准温度 | `298.15` | K | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `P_init` | 热力学基准压力 | `101325` | Pa | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `rtol` | 公共相对容差 | `1e-5` | 无量纲 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `atol` | 公共绝对容差 | `1e-8` | 随被比较量 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `root_two` | 二次方根 2 | `1.4142135623730951` | 无量纲 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `infNine` | 接近 1 的上界 | `1-rtol = 0.99999` | 无量纲 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `k` | Boltzmann 常数 | `1.380649e-23` | J/K | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `N_A` | Avogadro 常数 | `6.02214076e23` | 1/mol | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `R`, `gas_constant` | 摩尔气体常数及别名 | `N_A*k = 8.31446261815324` | J/(mol*K) | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `R2` | 气体常数平方 | `R*R = 69.1302886286676` | J2/(mol2*K2) | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `R_2` | 二分之一气体常数 | `0.5*R = 4.15723130907662` | J/(mol*K) | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `R_inv` | 气体常数倒数 | `1/R = 0.120272355042726` | mol*K/J | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `R_inv2` | 气体常数倒数平方 | `1/R2 = 0.0144654393875235` | mol2*K2/J2 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `warnStr` | 热力学公共错误前缀 | `"热力学错误"` | 字符串 | `thermo_supports/math_untils/thermodynamic_constant.py` |
| `func` | 通用立方型 EOS 公式字符串 | `(R*T)/(V-b)-((a*alpha)/(V**2+delta*V+epsilon))` | 公式模板 | `thermo_supports/math_untils/thermodynamic_constant.py` |

## 项目数学主常量

推荐引用：`thermo_supports.math_untils.math_constant`。

| 名称 | 含义 | 数值/表达式 | 单位 | 引用路径 |
|---|---|---|---|---|
| `third` | 三分之一 | `1/3` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `sixth` | 六分之一 | `1/6` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `ninth` | 九分之一 | `1/9` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `twelfth` | 十二分之一 | `1/12` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `two_thirds` | 三分之二 | `2/3` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `four_thirds` | 三分之四 | `4/3` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `root_three` | 二次方根 3 | `1.7320508075688772` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `one_27` | 二十七分之一 | `1/27` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `complex_factor` | `sqrt(3)/2*j` | `0.8660254037844386j` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `pi` | 圆周率 | `3.141592653589793` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |
| `e` | 自然常数 | `2.718281828459045` | 无量纲 | `thermo_supports/math_untils/math_constant.py` |

## `Fluids` 供应商兼容常量

`thermo_supports.Fluids.constants.constants` 是供应商兼容模块，仅在 `Fluids` 代码或已有
调用明确要求时引用。它重复定义 `R`、`N_A`、`k`、`pi`，新 operation 业务不要跨模块
混用重复定义。常用的供应商专属量如下：

| 名称 | 含义 | 数值 | 单位 | 引用路径 |
|---|---|---|---|---|
| `c` | 真空光速 | `299792458.0` | m/s | `thermo_supports/Fluids/constants/constants.py` |
| `g` | 标准重力加速度 | `9.80665` | m/s2 | `thermo_supports/Fluids/constants/constants.py` |
| `atm` | 标准大气压 | `101325.0` | Pa | `thermo_supports/Fluids/constants/constants.py` |
| `bar` | 巴 | `1e5` | Pa | `thermo_supports/Fluids/constants/constants.py` |
| `torr` | 托 | `atm/760` | Pa | `thermo_supports/Fluids/constants/constants.py` |
| `psi` | 磅力每平方英寸 | `pound*g/inch**2` | Pa | `thermo_supports/Fluids/constants/constants.py` |
| `zero_Celsius` | 摄氏零度的开尔文值 | `273.15` | K | `thermo_supports/Fluids/constants/constants.py` |
| `calorie` | 热化学卡 | `4.184` | J | `thermo_supports/Fluids/constants/constants.py` |
| `deg2rad` | 角度转弧度系数 | `0.017453292519943295769` | rad/degree | `thermo_supports/Fluids/constants/constants.py` |
| `rad2deg` | 弧度转角度系数 | `57.295779513082320877` | degree/rad | `thermo_supports/Fluids/constants/constants.py` |
