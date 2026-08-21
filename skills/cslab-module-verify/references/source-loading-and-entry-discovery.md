# 源码直载与测试入口发现

在需要确认目标 `.py` 实际被导入、隔离同名二进制或寻找项目测试入口时读取。

## 目标源码直载

只禁用目标模块的同名二进制，其他二进制依赖保持不变：

1. 解析目标 `.py` 与同目录 `X.cp37-win_amd64.pyd` 的绝对路径，确认都在目标模块目录内。
2. 确认备份名 `X.cp37-win_amd64.pyd1` 不存在；存在时停止，不能覆盖。
3. 将目标二进制改名为 `.pyd1`。这只是导入隔离，不是开发修改或交付成果。
4. 使用 `python -B` 或 `PYTHONDONTWRITEBYTECODE=1` 运行，避免生成 `.pyc` 验收产物。
5. 正常导入目标模块并输出或断言 `module.__file__` 的规范化绝对路径等于目标 `.py`。
6. 执行测试契约中的真实入口和验收工况；只检查路径不能证明算法通过。
7. 测试结束按开发者要求决定是否恢复二进制原名；恢复前再次确认不会覆盖现有文件。

不得读取、导入探测、反射或反编译被隔离二进制来补全实现。`.pyd1` 也不进入开发文件清单。

Windows 项目根目录示例：

```powershell
$env:PYTHONPATH='.'
uv run python -B <实际测试脚本>
```

测试代码应显式检查：

```python
import os
import target_package.target_module as target_module

actual = os.path.normcase(os.path.abspath(target_module.__file__))
expected = os.path.normcase(os.path.abspath(r"<目标.py绝对路径>"))
assert actual == expected, "实际加载的不是目标源码: %s" % actual
```

## 入口发现

优先使用开发者指定的测试入口。未指定时：

1. 在当前仓库检索 `pro`、`run()`、项目控制器类、`chemicalData`、`CalculateData`、目标
   模块名和目标 `startFun`。
2. 读取候选文件，核实其数据来源、控制器版本、计算模式、启动参数和退出方式。
3. 区分单独物性脚本、单模块脚本、完整项目入口和网页/服务器入口。
4. 向开发者展示真实存在的候选及差异并确认；没有候选时新建本次最小测试脚本，但不能
   把它写成平台固定路径。

不要假定 `123456.py`、`chemicalLib2/moduleRunBase.py` 或其他历史文件名存在。这里保留的
是测试形式，不是默认地址。

## 源码质量预检

先进行 Python 3.7.6 语法和导入检查，再运行通用审计：

```powershell
uv run python -m py_compile <目标.py>
uv run python .agents/skills/cslab-module-contract/scripts/audit_module_source.py `
  --family generic <目标.py>
```

审计脚本用于检查语法、中文模块/类/方法 docstring、残留 `print` 和明显未使用的私有成员。
动态入口、消费者和步长来源仍须结合实际模板、控制器和运行结果人工确认；历史 V1 模式
不能用于当前 Dynamic V4 新模块。
