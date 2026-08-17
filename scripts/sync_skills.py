# -*- coding: utf-8 -*-
"""单向同步 CSLab Skill 管理源，并用 SHA-256 检查运行副本漂移。"""

from __future__ import print_function

import argparse
import hashlib
import os
import shutil
import sys


IGNORED_NAMES = {"__pycache__"}
IGNORED_SUFFIXES = (".pyc", ".pyo")


def parse_args(argv=None):
    """解析管理源、运行副本、同步模式和可选 Skill 名称。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Skill 唯一管理源目录")
    parser.add_argument("--destination", required=True, help="Skill 运行副本目录")
    parser.add_argument("--sync", action="store_true", help="复制缺失或内容变化的管理源文件")
    parser.add_argument(
        "--skill", action="append", dest="skills",
        help="只检查或同步指定 Skill，可重复传入；默认处理全部 Skill",
    )
    return parser.parse_args(argv)


def file_hash(path):
    """分块计算文件 SHA-256。"""
    digest = hashlib.sha256()
    with open(path, "rb") as source_file:
        while True:
            chunk = source_file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root):
    """收集 Skill 目录中的相对文件路径，忽略 Python 缓存产物。"""
    result = {}
    for current_root, directory_names, file_names in os.walk(root):
        directory_names[:] = [name for name in directory_names if name not in IGNORED_NAMES]
        for file_name in file_names:
            if file_name.endswith(IGNORED_SUFFIXES):
                continue
            absolute = os.path.join(current_root, file_name)
            relative = os.path.relpath(absolute, root)
            result[relative] = absolute
    return result


def selected_skill_names(source, requested):
    """返回存在 SKILL.md 的全部或指定 Skill 目录名。"""
    available = sorted(
        name for name in os.listdir(source)
        if os.path.isfile(os.path.join(source, name, "SKILL.md"))
    )
    if not requested:
        return available
    missing = sorted(set(requested) - set(available))
    if missing:
        raise ValueError("管理源不存在 Skill: %s" % ", ".join(missing))
    return sorted(set(requested))


def compare_skill(source_root, destination_root, skill_name, do_sync):
    """比较一个 Skill，必要时从管理源复制到运行副本。"""
    source_skill = os.path.join(source_root, skill_name)
    destination_skill = os.path.join(destination_root, skill_name)
    source_files = collect_files(source_skill)
    destination_files = collect_files(destination_skill) if os.path.isdir(destination_skill) else {}
    changed = []

    for relative, source_file in sorted(source_files.items()):
        destination_file = os.path.join(destination_skill, relative)
        different = relative not in destination_files
        if not different:
            different = file_hash(source_file) != file_hash(destination_file)
        if different:
            changed.append(relative)
            if do_sync:
                parent = os.path.dirname(destination_file)
                if not os.path.isdir(parent):
                    os.makedirs(parent)
                shutil.copy2(source_file, destination_file)

    extras = sorted(set(destination_files) - set(source_files))
    if extras:
        print("[WARN] %s 运行副本存在管理源没有的文件: %s" % (
            skill_name, ", ".join(extras),
        ))
    if changed:
        action = "已同步" if do_sync else "存在漂移"
        print("[%s] %s: %s" % (action, skill_name, ", ".join(changed)))
    elif not extras:
        print("[一致] %s" % skill_name)
    return changed, extras


def main(argv=None):
    """执行单向同步或只读一致性检查。"""
    args = parse_args(argv)
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination)
    if not os.path.isdir(source):
        print("管理源目录不存在: %s" % source, file=sys.stderr)
        return 2
    if source == destination:
        print("管理源和运行副本不能是同一目录", file=sys.stderr)
        return 2
    try:
        skill_names = selected_skill_names(source, args.skills)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    drift_count = 0
    extra_count = 0
    for skill_name in skill_names:
        changed, extras = compare_skill(source, destination, skill_name, args.sync)
        drift_count += len(changed)
        extra_count += len(extras)

    if args.sync:
        print("同步完成：%s 个文件已更新，%s 个额外文件未删除" % (drift_count, extra_count))
        return 1 if extra_count else 0
    print("检查完成：%s 个漂移文件，%s 个额外文件" % (drift_count, extra_count))
    return 1 if drift_count or extra_count else 0


if __name__ == "__main__":
    sys.exit(main())
