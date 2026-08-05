---
name: cslab-module-verify
description: Use when locally testing or debugging a CSLab domain/operation module - the __main__ scaffold, obtainData data fetching, environment constraints, verification checklist, and deployment notes.
---

# 业务模块本地验证

## 环境硬约束(先读)

- 固定使用 **Python 3.7.6** 和项目锁定依赖。编译依赖必须与当前平台和解释器 ABI
  匹配：Windows 使用 `*.cp37-win_amd64.pyd`，Linux 使用对应 CPython 3.7 `.so`。
- 开发部门通常在大量 `.pyd/.so` 依赖下工作，只修改自己负责范围内保留的 `.py`
  源码。编译依赖视为稳定公开能力，不读取、修改、反编译、反射或试探其内部实现；调用
  契约以项目 Skill 为准。
- 当前平台存在匹配二进制时正常运行验证。只有缺少兼容二进制、依赖服务或必要测试数据
  时才退化为**静态审查**：按 `cslab-module-contract` 与所属族包逐项核对，并明确说明
  “未运行验证”及具体原因，不得笼统归因于操作系统。
- 取数接口 `obtainData/` 免鉴权,但需要能访问 `${CSLAB_SERVER_HOST}`。

## 取数接口

- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/chemicalData/`
  body:`{"pro": <项目id>, "rely_cal_data_type": {"relyState": "RelyAll", "relyDataType": [], "方法包": [<Method_bag>]}}`
  (`rely_cal_data_type` 可省略,缺省取全部)
  → 物性/组分/方法包数据(喂给 `instantiation_data`)。
- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/calModuleData/`
  → 模块/流股/执行顺序数据。
- `pro` 是项目 id(32 位 hex),由开发者提供一个含目标组分与方法包的测试项目。
- 历史脚本里的 `"calData"` 端点在当前服务端无对应实现,新脚手架不要用。

## __main__ 脚手架模板

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

## 验证检查单

跑通后逐项核对,并把结论写进交付说明:

1. `Run()` 返回 `(bool, dict)` 二元组,成功分支返回 `(True, self.result)`。
2. `result` 外层是 `{"result": {...}}`,键与需求约定一致,`unitType` 拼写正确。
3. 模板中 `is_input=否` 的每个属性,`Run()` 后同名实例属性确有值(落库通道)。
4. 出口流股字段写全:`F_mol/P_in/T/XI_mol/GasRat`,物料衡算闭合
   (`FL_mol + FV_mol == F_mol`,组成非负、归一)。
5. 初值复用:同参数连跑两次结果一致且第二次更快;改输入后重跑不复用旧 `K0`。
6. 边界工况:全液(`VF=0`)、全汽(`VF=1`)、单组分、含零组分进料不崩溃,
   告警走 `feedback`。
7. 失败路径:空流量/空组分/条件不足时返回 `(False, {})` 且有对应 feedback 码。
8. 无 `print` 残留,无未定义变量分支(静态过一遍所有 if 分支)。

## 整图联调(可选,成本高)

`chemical-scheduler` 的 `runServerLocal` 可本地跑整张画布:数据来自
`data/calculateDependData/<项目>/` 下的 YAML(先对线上项目 POST
`obtainData/calModuleData|chemicalData` 导出保存),且依赖 etcd 服务。
仅在需要验证多模块耦合/执行顺序时使用;单模块一律用 `__main__` 脚手架。

## 部署与登记

1. 新 `.py` 落到服务器**根 `domain/operation/`**(scheduler 经符号链接可见),
   无需编译 `.so`;**没有上传 API**,文件走部署渠道。
2. 模板算法槽位(如 `steady_module`)指向 `operation.<文件名>`(类名不同时
   `operation.<文件名>;<类名>`),`startFun` 与入口方法严格同名——拼错不会报错,
   会静默按成功处理,必须人工核对。
3. 上线前在测试项目里从前端触发一次计算,确认前端展示、落库属性、下游流股三条
   通道都有值。
