# -*- coding: utf-8 -*-
"""审计 CSLab 算法源码的文档完整性、明显冗余和动态 V1 契约。"""

from __future__ import print_function

import argparse
import ast
import io
import re
import sys


CHINESE_RE = re.compile(u"[\u4e00-\u9fff]")


class Finding(object):
    """保存一条静态审计发现。"""

    def __init__(self, level, code, line, message):
        """记录级别、规则编号、源码行号和中文说明。"""
        self.level = level
        self.code = code
        self.line = line
        self.message = message


def parse_args(argv=None):
    """解析目标文件、模块族和严格模式参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="待审计的 Python 源码路径")
    parser.add_argument(
        "--family", choices=("generic", "dynamic-v1"), default="generic",
        help="选择通用规则或 DynamicCalculateControlV1 专项规则",
    )
    parser.add_argument(
        "--allow-result", action="store_true",
        help="已从实际控制器确认返回值消费者时，允许动态模块定义和返回结果",
    )
    parser.add_argument(
        "--strict", action="store_true", help="将警告也视为失败",
    )
    return parser.parse_args(argv)


def read_source(path):
    """以 UTF-8-SIG 读取源码，兼容带 BOM 的 Python 文件。"""
    with io.open(path, "r", encoding="utf-8-sig") as source_file:
        return source_file.read()


def add_doc_finding(findings, node, label):
    """检查模块、类、函数或方法是否具有中文且不过度简略的 docstring。"""
    doc = ast.get_docstring(node, clean=False)
    line = getattr(node, "lineno", 1)
    if not doc:
        findings.append(Finding("ERROR", "DOC001", line, "%s缺少 docstring" % label))
        return
    if not CHINESE_RE.search(doc):
        findings.append(Finding("ERROR", "DOC002", line, "%s的 docstring 不含中文" % label))
        return
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        statement_count = max(len(node.body) - 1, 0)
        chinese_count = len(CHINESE_RE.findall(doc))
        if statement_count >= 4 and chinese_count < 18:
            findings.append(Finding(
                "WARN", "DOC003", line,
                "%s逻辑不短，但 docstring 可能未覆盖参数、返回、状态、异常和步骤" % label,
            ))


def is_self_attribute(node, attribute_name=None):
    """判断 AST 节点是否为 self 的直接属性访问。"""
    if not isinstance(node, ast.Attribute):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id != "self":
        return False
    return attribute_name is None or node.attr == attribute_name


def subscript_key(node):
    """兼容 Python 3.7 与高版本 AST，提取下标常量。"""
    if not isinstance(node, ast.Subscript):
        return None
    slice_node = node.slice
    if hasattr(ast, "Index") and isinstance(slice_node, ast.Index):
        slice_node = slice_node.value
    if isinstance(slice_node, ast.Str):
        return slice_node.s
    if isinstance(slice_node, ast.Constant):
        return slice_node.value
    return None


def is_pgv_dt(node):
    """判断表达式是否严格读取 self.Data.PGV["DT"]。"""
    if not isinstance(node, ast.Subscript) or subscript_key(node) != "DT":
        return False
    pgv = node.value
    return (
        isinstance(pgv, ast.Attribute)
        and pgv.attr == "PGV"
        and isinstance(pgv.value, ast.Attribute)
        and pgv.value.attr == "Data"
        and isinstance(pgv.value.value, ast.Name)
        and pgv.value.value.id == "self"
    )


def function_nodes(tree):
    """返回源码中全部顶层函数和类方法。"""
    nodes = []
    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append((item, "函数 %s" % item.name))
        elif isinstance(item, ast.ClassDef):
            for child in item.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nodes.append((child, "方法 %s.%s" % (item.name, child.name)))
    return nodes


def audit_common(tree):
    """执行所有算法源码共享的静态检查。"""
    findings = []
    add_doc_finding(findings, tree, "模块")

    for item in tree.body:
        if isinstance(item, ast.ClassDef):
            add_doc_finding(findings, item, "类 %s" % item.name)
    for node, label in function_nodes(tree):
        add_doc_finding(findings, node, label)

    private_methods = {}
    private_calls = set()
    private_stores = {}
    private_loads = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            findings.append(Finding("ERROR", "DBG001", node.lineno, "存在残留 print 调试输出"))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_") and not node.name.startswith("__"):
            private_methods[node.name] = node.lineno
        if isinstance(node, ast.Call) and is_self_attribute(node.func):
            private_calls.add(node.func.attr)
        if isinstance(node, ast.Attribute) and node.attr.startswith("_") and not node.attr.startswith("__"):
            if is_self_attribute(node):
                if isinstance(node.ctx, ast.Store):
                    private_stores.setdefault(node.attr, node.lineno)
                elif isinstance(node.ctx, ast.Load):
                    private_loads.add(node.attr)

    for name, line in sorted(private_methods.items()):
        if name not in private_calls:
            findings.append(Finding(
                "WARN", "MIN001", line,
                "私有方法 %s 未发现类内消费者，请确认是否应删除或内联" % name,
            ))
    for name, line in sorted(private_stores.items()):
        if name not in private_loads:
            findings.append(Finding(
                "WARN", "MIN002", line,
                "私有状态 self.%s 只写未读，请确认是否为无用状态" % name,
            ))
    return findings


def audit_dynamic_v1(tree, allow_result):
    """执行 DynamicCalculateControlV1 返回值和 PGV 步长专项检查。"""
    findings = []
    run_nodes = [node for node, _ in function_nodes(tree) if node.name == "Run"]
    drun_nodes = [node for node, _ in function_nodes(tree) if node.name == "DRun"]
    if not drun_nodes:
        findings.append(Finding("ERROR", "DYN001", 1, "Dynamic V1 模块缺少 DRun 方法"))
        return findings

    if not allow_result:
        for node, _ in function_nodes(tree):
            if node.name in ("result", "result_fail"):
                findings.append(Finding(
                    "ERROR", "DYN002", node.lineno,
                    "Dynamic V1 未声明返回消费者，不应定义 %s" % node.name,
                ))
        for node in ast.walk(tree):
            if (
                    (is_self_attribute(node, "result") or is_self_attribute(node, "result_fail"))
                    and isinstance(node.ctx, ast.Store)):
                findings.append(Finding(
                    "ERROR", "DYN005", node.lineno,
                    "Dynamic V1 未声明返回消费者，不应构造 self.%s" % node.attr,
                ))

        for entry in run_nodes + drun_nodes:
            for node in ast.walk(entry):
                if isinstance(node, ast.Return) and node.value is not None:
                    findings.append(Finding(
                        "ERROR", "DYN003", node.lineno,
                        "Dynamic V1 的 %s 返回值无消费者，不应通过返回值传递业务或失败信息"
                        % entry.name,
                    ))

    for drun in drun_nodes:
        has_pgv_assignment = False
        for node in ast.walk(drun):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                value = node.value
                if any(isinstance(target, ast.Name) and target.id == "dt" for target in targets):
                    if is_pgv_dt(value):
                        has_pgv_assignment = True
        if not has_pgv_assignment:
            findings.append(Finding(
                "ERROR", "DYN004", drun.lineno,
                "DRun 未执行 dt = self.Data.PGV[\"DT\"]，不能使用外部兼容步长",
            ))
    return findings


def main(argv=None):
    """运行审计并以非零退出码表示错误或严格模式下的警告。"""
    args = parse_args(argv)
    if not args.source.lower().endswith(".py"):
        print("[ERROR] SRC001 line 1: 目标开发文件必须是 .py", file=sys.stderr)
        return 2
    try:
        source = read_source(args.source)
        tree = ast.parse(source, filename=args.source)
    except (IOError, OSError, UnicodeError, SyntaxError) as exc:
        print("[ERROR] SRC002 line 1: 无法读取或解析源码: %s" % exc, file=sys.stderr)
        return 2

    findings = audit_common(tree)
    if args.family == "dynamic-v1":
        findings.extend(audit_dynamic_v1(tree, args.allow_result))

    findings.sort(key=lambda item: (item.line, item.level, item.code))
    for item in findings:
        print("[%s] %s line %s: %s" % (item.level, item.code, item.line, item.message))

    error_count = len([item for item in findings if item.level == "ERROR"])
    warning_count = len([item for item in findings if item.level == "WARN"])
    print("审计完成：%s 个错误，%s 个警告" % (error_count, warning_count))
    if error_count or (args.strict and warning_count):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
