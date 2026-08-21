# 物性与单模块测试

在执行 `pro + Method_bag` 物性验证或稳态业务单模块验证时读取。

## 服务端取数形式

- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/chemicalData/`：按 `pro` 和必要的
  `Method_bag` 获取组分、物性和方法包数据，再交给 `instantiation_data(...)`。
- `POST ${CSLAB_SERVER_HOST}/cslab-server/obtainData/CalculateData/`：获取模块属性、节点、
  流股和执行顺序；也可使用项目已有 `HttpLoadData(host).load_module_data(payload)`。
- `obtainData/` 免鉴权，但必须能访问当前 `CSLAB_SERVER_HOST`。
- `pro` 由开发者提供，须包含目标组分和方法包。历史 `calData` 不是当前有效端点，新脚本
  不使用。

典型 `chemicalData` 请求体：

```json
{
  "pro": "<项目编号>",
  "rely_cal_data_type": {
    "relyState": "RelyAll",
    "relyDataType": [],
    "方法包": ["<Method_bag>"]
  }
}
```

## 单独物性验证

1. 用测试契约中的 `pro` 与 `Method_bag` 获取 `chemicalData`。
2. `json.loads(...)` 后调用 `instantiation_data(**chemical_data)` 构造 `Data`。
3. 按所属物性 Skill 选择 `Flash`、`MethodLV` 或具体公开对象，不能探测二进制接口。
4. 统一调用 `phy_prop`；矩阵工况仍通过它传入数组，不直接调用 `phy_propArray` 或
   `CalculateArray`。严格遵守属性要求的参数、单位、shape 和组分坐标。
5. 对比参考值、旧标量路径、误差阈值或已确认物理约束，并报告实际误差。

脚本保存位置由当前任务决定，不能把参考脚本路径固化为平台契约。

## 稳态单模块脚手架

以下仅用于已确认入口返回消费者的稳态模块。类名、端口、构造参数、Flow 初态和验收项
必须按真实模板替换；不得套用于不消费返回值的动态模块。

```python
if __name__ == "__main__":
    import json

    from domain.getdata.complAll import compl_init, instantiation_data
    from domain.getdata.obtain_data import RequestsServer
    from domain.operation.Flow import Flow

    pro = "<测试项目编号>"
    method_bag = "<开发者确认的方法包编号>"
    chemical_data = json.loads(
        RequestsServer().post_request(
            {
                "pro": pro,
                "rely_cal_data_type": {
                    "relyState": "RelyAll",
                    "relyDataType": [],
                    "方法包": [method_bag],
                },
            },
            "chemicalData",
        )["data"]
    )
    data: compl_init = instantiation_data(**chemical_data)

    inlet = Flow(Data=data, Method_bag=method_bag)
    outlet = Flow(Data=data, Method_bag=method_bag)
    inlet.flow_prop(
        T=<温度_K>,
        P_in=<压力_Pa>,
        XI_mol=<与Data.comp同序的组成>,
        F_mol=<摩尔流量>,
    )

    module = TargetModule(
        Data=data,
        Method_bag=method_bag,
        FFin=inlet,
        FFout=outlet,
        # 其余参数严格来自当前模板契约。
    )
    module.feedback = lambda *args, **kwargs: None
    state, result = module.Run()
```

## 单模块核对重点

- 组成向量长度和顺序与 `Data.comp` 一致，不能混用全局与局部坐标。
- 上游 Flow 先具备真实入口状态，避免模块读取未初始化字段。
- 反应类模块只在契约要求时传入当前项目反应列表。
- 本地 feedback 空桩只替代框架注入，不得改变错误传播或测试预期。
- 只核对真实消费者：返回值、同名实例属性和出口节点不能互相替代。
- 验证质量、组分、能量或其他已选衡算，以及正常、边界和退化工况。
