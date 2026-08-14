#!/usr/bin/env python3
"""把各子文件夹里的 TIFF 复制到一个输出文件夹。

目录约定（默认只看一层子文件夹）：

    输入目录/
      子文件夹A/
        某个文件夹/          # 忽略
        slice_001.tif        # 复制
      子文件夹B/
        某个文件夹/
        slice_002.tif
      ...

    输出目录/
      子文件夹A_slice_001.tif
      子文件夹B_slice_002.tif

默认会在文件名前加上所属子文件夹名，避免重名覆盖。

用法示例：

    python collect_tiffs.py /path/to/parent_dir -o /path/to/all_tiffs
    python collect_tiffs.py /path/to/parent_dir -o /path/to/all_tiffs --dry-run
    python collect_tiffs.py /path/to/parent_dir -o /path/to/all_tiffs --keep-names
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

TIFF_SUFFIXES = {".tif", ".tiff", ".TIF", ".TIFF"}


def natural_key(text: str):
    """按数字大小排序，避免 sample_10 排在 sample_2 前面。"""
    parts = re.split(r"(\d+)", text)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def find_tiffs(input_dir: Path, recursive: bool) -> list[Path]:
    """收集每个一级子文件夹里的 TIFF（默认不进入更深层目录）。"""
    if not input_dir.is_dir():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    tiffs: list[Path] = []
    subdirs = sorted(
        [p for p in input_dir.iterdir() if p.is_dir()],
        key=lambda p: natural_key(p.name),
    )

    if not subdirs:
        tiffs.extend(p for p in input_dir.iterdir() if p.is_file() and p.suffix in TIFF_SUFFIXES)
        return tiffs

    for subdir in subdirs:
        if recursive:
            found = sorted(
                (p for p in subdir.rglob("*") if p.is_file() and p.suffix in TIFF_SUFFIXES),
                key=lambda p: natural_key(str(p.relative_to(input_dir))),
            )
        else:
            found = sorted(
                (p for p in subdir.iterdir() if p.is_file() and p.suffix in TIFF_SUFFIXES),
                key=lambda p: natural_key(p.name),
            )
        if not found:
            print(f"警告: {subdir} 中没有找到 TIFF，已跳过", file=sys.stderr)
            continue
        if len(found) > 1 and not recursive:
            print(
                f"警告: {subdir} 中有 {len(found)} 个 TIFF，将全部复制",
                file=sys.stderr,
            )
        tiffs.extend(found)

    return tiffs


def unique_name(name: str, used: set[str]) -> str:
    if name not in used:
        used.add(name)
        return name
    stem = Path(name).stem
    suffix = Path(name).suffix
    i = 2
    while True:
        candidate = f"{stem}_{i}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        i += 1


def dest_filename(src: Path, input_dir: Path, keep_names: bool, used: set[str]) -> str:
    if keep_names:
        return unique_name(src.name, used)
    try:
        parent = src.parent.relative_to(input_dir)
        prefix = "_".join(parent.parts) if parent.parts else input_dir.name
    except ValueError:
        prefix = src.parent.name
    return unique_name(f"{prefix}_{src.name}", used)


def copy_tiffs(
    tiffs: list[Path],
    input_dir: Path,
    output_dir: Path,
    dry_run: bool,
    keep_names: bool,
) -> None:
    if not tiffs:
        raise FileNotFoundError("没有找到任何 TIFF 文件")

    if output_dir.resolve() == input_dir.resolve():
        raise ValueError("输出目录不能和输入目录相同")

    used: set[str] = set()
    jobs: list[tuple[Path, Path]] = []
    for src in tiffs:
        dest = output_dir / dest_filename(src, input_dir, keep_names, used)
        jobs.append((src, dest))

    print(f"共找到 {len(jobs)} 个 TIFF，复制计划如下：")
    for src, dest in jobs:
        print(f"  {src}  ->  {dest.name}")

    if dry_run:
        print("dry-run：未复制文件")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for src, dest in jobs:
        shutil.copy2(src, dest)
    print(f"已复制 {len(jobs)} 个 TIFF 到: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="遍历子文件夹，把找到的 TIFF 复制到另一个文件夹",
    )
    parser.add_argument("input_dir", type=Path, help="包含多个子文件夹的根目录")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("collected_tiffs"),
        help="输出文件夹（默认: ./collected_tiffs）",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="进入子文件夹内部继续搜索 TIFF（默认只取每个子文件夹顶层的 TIFF）",
    )
    parser.add_argument(
        "--sort",
        choices=("folder", "name"),
        default="folder",
        help="folder=按子文件夹名排序（默认）；name=按 TIFF 文件名排序",
    )
    parser.add_argument(
        "--keep-names",
        action="store_true",
        help="保持原文件名；若重名则自动加 _2、_3 后缀",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只列出将要复制的文件，不实际复制",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    tiffs = find_tiffs(input_dir, recursive=args.recursive)
    if args.sort == "name":
        tiffs = sorted(tiffs, key=lambda p: natural_key(p.name))
    try:
        copy_tiffs(
            tiffs,
            input_dir=input_dir,
            output_dir=args.output.resolve(),
            dry_run=args.dry_run,
            keep_names=args.keep_names,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
