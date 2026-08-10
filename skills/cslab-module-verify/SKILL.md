---
name: cslab-module-verify
description: Use when locally testing or debugging any CSLab algorithm module, including single-module tests, direct Python source loading, dynamic/full-flow execution through chemicalLib/moduleRunBase.py, obtainData fetching, verification checklists, process cleanup, and deployment notes.
---

# CSLab 算法模块本地验证

## 环境硬约束(先读)

- 先遵守 `cslab-module-develop` 的“开发文件边界”：本 Skill 的目标开发文件、源码验证
  对象和算法交付物只能是 `.py`；`.pyd` 不能作为开发文件或源码完成证明。
- 固定使用 **Python 3.7.6** 和项目锁定依赖。编译依赖必须与当前平台和解释器 ABI
  匹配：Windows 使用 `*.cp37-win_amd64.pyd`，Linux 使用对应 CPython 3.7 `.so`。
- 开发部门通常在大量 `.pyd/.so` 依赖下工作，只修改自己负责范围内保留的 `.py`
  源码。编译依赖视为稳定公开能力，不读取、修改、反编译、反射或试探其内部实现；调用
  契约以项目 Skill 为准。
- 当前平台存在匹配二进制时正常运行验证。只有缺少兼容二进制、依赖服务或必要测试数据
  时才退化为**静态审查**：按 `cslab-module-contract` 与所属族包逐项核对，并明确说明
  “未运行验证”及具体原因，不得笼统归因于操作系统。
- 取数接口 `obtainData/` 免鉴权,但需要能访问 `${CSLAB_SERVER_HOST}`。

## 目标源码直载验证

开发者要求验证新 `.py` 时，只禁用**同模块同名**目标二进制，其他依赖二进制保持不变：

1. 将目标 `X.cp37-win_amd64.pyd` 改名为 `X.cp37-win_amd64.pyd1`，先确认目标名不存在；
2. 创建或修改 `X.py`，不编译目标模块，不读取、反编译、反射或探测原二进制；
3. 使用 `python -B` 或 `PYTHONDONTWRITEBYTECODE=1` 防止生成 `.pyc` 验收产物；
4. 正常导入后检查模块 `__file__` 指向本地 `X.py`；这只证明导入来源，不探测实现；
5. 测试结束按开发者要求决定是否恢复原文件名，不擅自覆盖已有文件。

临时改名只用于排除 Python 对同名二进制的导入优先级，不能计为算法修改，不能进入开发
成果、交付文件或完成项。验收结论必须来自实际加载并执行的 `X.py`。

Windows 项目根目录运行脚本时使用：

```powershell
$env:PYTHONPATH='.'
uv run python -B <脚本路径>
```

## 取数接口

- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/chemicalData/`
  body:`{"pro": <项目id>, "rely_cal_data_type": {"relyState": "RelyAll", "relyDataType": [], "方法包": [<Method_bag>]}}`
  (`rely_cal_data_type` 可省略,缺省取全部)
  → 物性/组分/方法包数据(喂给 `instantiation_data`)。
- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/CalculateData/`
  → 项目模块属性、节点连接、流股和执行顺序数据；也可使用
  `HttpLoadData(host).load_module_data(payload)`。
- `pro` 是项目 id(32 位 hex),由开发者提供一个含目标组分与方法包的测试项目。
- 历史脚本里的 `"calData"` 端点在当前服务端无对应实现,新脚手架不要用。

## 稳态业务单模块脚手架

放在模块文件末尾,单模块验证的标准范式(取数 → 建 Data → 建 Flow → 建模块 →
`get_value` → `Run` → 看 `result`):

```python
if __name__ == "__main__":
    from domain.getdata.obtain_data import RequestsServer
    from domain.getdata.complAll import *
    from domain.operation.Flow import Flow
    import json, time

    pro = "<测试项目id>"
    chemical_data = json.loads(
        RequestsServer().post_request({"pro": pro}, "chemicalData")["data"])
    Data: compl_init = instantiation_data(**chemical_data)
    Method_bag = list(Data.binaryData_all.keys())[0]
    print("组分:", {i["cas"]: i["alias"] for i in Data.comp})

    fin = Flow(Data=Data, Method_bag=Method_bag)
    dout = Flow(Data=Data, Method_bag=Method_bag)
    wout = Flow(Data=Data, Method_bag=Method_bag)
    fin.flow_prop(T=350, P_in=101325, XI_mol=[0, 0.5, 0.5, 0, 0], F_mol=10)

    m = MyTank(Data=Data, Method_bag=Method_bag,
               FFin=fin, FDout=dout, FWout=wout,
               Input_type1="温度", Input_value1=370,
               Input_type2="压力", Input_value2=101325,
               mode=0, Height=2, Diameter=1)
    m.feedback = feedback_func          # 本地空桩,替代框架注入
    t0 = time.time()
    m.get_value()
    state, result = m.Run()
    print("耗时 %.3f s" % (time.time() - t0), state)
    print(result)
```

要点:

1. 组成向量长度必须等于测试项目的组分数,顺序与 `Data.comp` 一致。
2. 反应类模块传 `RList=list(Data.ReactionData.keys())`。
3. 本地必须挂 feedback 空桩,否则调用 `self.feedback` 时 AttributeError。
4. 入口流股要先赋好状态(`flow_prop` 或先 `Run()` 上游 Feed),保证 `FFin.FH`
   等字段可用,再跑本模块。

## 通用验证检查单

跑通后逐项核对,并把结论写进交付说明:

1. `Run()` 返回 `(bool, dict)` 二元组,成功分支返回 `(True, self.result)`。
2. `result` 外层是 `{"result": {...}}`,键与需求约定一致,`unitType` 拼写正确。
3. 模板中 `is_input=否` 的每个属性,`Run()` 后同名实例属性确有值(落库通道)。
4. 按模板和所属族契约写全出口节点字段；逐项验证质量、组分、能量或其他已选衡算闭合。
5. 同输入重复运行结果一致；存在缓存/暖启动时验证改输入后不会复用失效状态。
6. 覆盖所属模型的正常、边界和退化工况，数值非负性、归一性及上下限符合已确认方案。
7. 空输入、条件不足、不收敛或不支持分支返回受控失败，告警走 `feedback`。
8. 无 `print` 残留,无未定义变量分支(静态过一遍所有 if 分支)。
9. 逐项验证开发者选择的模型、假设、初始条件、边界条件和验收标准；报告方程闭合误差。
10. 源码的模块说明、方法注释、方程变量表和实际实现一致，不能保留已否决方案描述。
11. 目标模块 `__file__` 明确指向 `.py`；已有同名 `.pyd` 能运行不能替代源码验收。

不同模块族在以上通用项之上加载各自检查单；例如闪蒸模块检查相态与焓流，动态模块
检查时间序列、状态连续性和守恒关系，不能把某一设备族的出口字段当作所有模块通用要求。

## 本地整图与动态联调

服务器网页只负责画布、模板实例值和物性数据；本地测试由本机 Python 进程加载本地
`chemicalLib/` 与 `domain/` 文件。不得把网页服务器运行结果当作本地源码验收结果。

当前项目可在根目录直接运行：

```powershell
$env:PYTHONPATH='.'
uv run python -B chemicalLib/moduleRunBase.py
```

运行前在 `moduleRunBase.py` 核对 `host/pro/callow_way/pk`。动态 `run()` 会持续等待退出
信号，测试必须记录本次启动的 PID，采用受控停止，并只清理本次进程。工具调用被中断后
立即检查残留 `uv/python` 进程，不影响其他项目服务。

动态 V1 在算法调用期间重定向 stdout 并抑制 `RuntimeWarning`，模块内 `print` 可能不可见。
临时状态观测使用现有 logger 或在重定向范围外采集，日志至少包含时间、关键状态和衡算
输入/输出；确认成功后删除临时代码并做最终回归。

整图验证至少确认：本地目标 `.py` 被加载、执行顺序正确、关键状态随时间符合所选模型、
守恒误差在容差内、上下游边界得到更新、退出后无残留进程。

## 离线整图联调

`chemical-scheduler` 的 `runServerLocal` 可本地跑整张画布:数据来自
`data/calculateDependData/<项目>/` 下的 YAML(先对线上项目 POST
`obtainData/CalculateData|chemicalData` 导出保存),且依赖 etcd 服务。
仅在需要验证多模块耦合/执行顺序时使用;单模块一律用 `__main__` 脚手架。

## 部署与登记

1. 新 `.py` 落到模板槽位对应的 `domain/<目录>/`；例如 `operation.X` 对应
   `domain/operation/X.py`，`dynamic.X` 对应 `domain/dynamic/X.py`。没有上传 API，
   文件走部署渠道。
2. 模板算法槽位指向 `<目录>.<文件名>`(类名不同时
   `<目录>.<文件名>;<类名>`),`startFun` 与入口方法严格同名——拼错不会报错,
   会静默按成功处理,必须人工核对。
3. 上线前在测试项目里从前端触发一次计算,确认前端展示、落库属性、下游流股三条
   通道都有值。
