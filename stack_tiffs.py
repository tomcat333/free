#!/usr/bin/env python3
"""将各子文件夹中的二维 TIFF 叠成三维栈，方便 ImageJ 等软件打开。

目录约定（默认只看一层子文件夹）：

    输入目录/
      子文件夹A/
        某个文件夹/          # 忽略
        slice_001.tif        # 取出
      子文件夹B/
        某个文件夹/
        slice_002.tif
      ...

用法示例：

    python stack_tiffs.py /path/to/parent_dir -o stack.tif
    python stack_tiffs.py /path/to/parent_dir -o stack.tif --dry-run
    python stack_tiffs.py /path/to/parent_dir -o stack.tif --dtype float32
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import tifffile

TIFF_SUFFIXES = {".tif", ".tiff", ".TIF", ".TIFF"}
# tifffile 的 ImageJ 格式只支持这四种：uint8(B)、uint16(H)、int16(h)、float32(f)
IMAGEJ_DTYPE_CHARS = set("BHhf")
IMAGEJ_DTYPE_NAMES = ("uint8", "uint16", "int16", "float32")


def natural_key(text: str):
    """按数字大小排序，避免 slice_10 排在 slice_2 前面。"""
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
        # 输入目录本身就放 TIFF 时也能用
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
                f"警告: {subdir} 中有 {len(found)} 个 TIFF，将全部纳入栈中",
                file=sys.stderr,
            )
        tiffs.extend(found)

    return tiffs


def read_as_2d_or_pages(path: Path) -> list[np.ndarray]:
    """读取 TIFF。二维图作为一层；若已是多页，则拆成多层并给出提示。"""
    with tifffile.TiffFile(path) as tf:
        data = tf.asarray()

    if data.ndim == 2:
        return [data]
    if data.ndim == 3:
        # (Z, Y, X) 或 (Y, X, C)
        if data.shape[-1] in (3, 4) and data.shape[0] not in (3, 4):
            return [data]
        print(f"提示: {path.name} 已是 {data.shape[0]} 页，将全部叠入", file=sys.stderr)
        return [data[i] for i in range(data.shape[0])]
    if data.ndim == 4:
        print(f"提示: {path.name} 形状为 {data.shape}，按第一维拆层", file=sys.stderr)
        return [data[i] for i in range(data.shape[0])]

    raise ValueError(f"不支持的 TIFF 维度 {data.ndim} ({path})")


def validate_layers(layers: list[np.ndarray], source_names: list[str]) -> None:
    shapes = {layer.shape for layer in layers}
    dtypes = {layer.dtype for layer in layers}
    if len(shapes) > 1:
        detail = ", ".join(f"{name}:{layer.shape}" for name, layer in zip(source_names, layers))
        raise ValueError(
            "各 TIFF 尺寸不一致，无法直接叠成三维栈。请先裁剪/缩放统一尺寸。\n" + detail
        )
    if len(dtypes) > 1:
        print(
            f"提示: 像素类型不一致 {sorted(str(d) for d in dtypes)}，将统一为第一张的 {layers[0].dtype}",
            file=sys.stderr,
        )


def to_imagej_dtype(stack: np.ndarray, requested: str = "auto") -> np.ndarray:
    """把像素类型转成 ImageJ 能写进超栈的那几种。

    原始 TIFF 经常是 int32（numpy 记作 'i'），ImageJ 格式不支持，会直接报错。
    auto：已兼容则保持；整数且落在 0–65535 则用 uint16，否则用 float32。
    """
    if requested != "auto":
        target = np.dtype(requested)
        if stack.dtype != target:
            print(f"提示: 按指定将 {stack.dtype} 转为 {target}", file=sys.stderr)
        return stack.astype(target, copy=False)

    if stack.dtype.char in IMAGEJ_DTYPE_CHARS:
        return stack

    vmin = stack.min()
    vmax = stack.max()
    if np.issubdtype(stack.dtype, np.integer) and vmin >= 0 and vmax <= np.iinfo(np.uint16).max:
        target = np.dtype(np.uint16)
    else:
        target = np.dtype(np.float32)

    print(
        f"提示: ImageJ 不支持 {stack.dtype}（dtype '{stack.dtype.char}'），"
        f"已按数值范围 [{vmin}, {vmax}] 转为 {target}",
        file=sys.stderr,
    )
    return stack.astype(target, copy=False)


def stack_and_write(
    tiffs: list[Path],
    output: Path,
    dry_run: bool,
    dtype: str = "auto",
) -> None:
    if not tiffs:
        raise FileNotFoundError("没有找到任何 TIFF 文件")

    print(f"共找到 {len(tiffs)} 个 TIFF，叠层顺序如下：")
    for i, path in enumerate(tiffs, start=1):
        print(f"  [{i:04d}] {path}")

    if dry_run:
        print("dry-run：未写入文件")
        return

    layers: list[np.ndarray] = []
    source_names: list[str] = []
    for path in tiffs:
        pages = read_as_2d_or_pages(path)
        layers.extend(pages)
        source_names.extend([path.name] * len(pages))

    validate_layers(layers, source_names)

    target_dtype = layers[0].dtype
    stack = np.stack([layer.astype(target_dtype, copy=False) for layer in layers], axis=0)
    stack = to_imagej_dtype(stack, requested=dtype)

    output.parent.mkdir(parents=True, exist_ok=True)
    # ImageJ 可直接打开的多页 TIFF；体积较大时用 BigTIFF
    bigtiff = stack.nbytes > 4 * 1024**3
    tifffile.imwrite(
        output,
        stack,
        imagej=True,
        metadata={"axes": "ZYX" if stack.ndim == 3 else "ZYXC"},
        compression=None,
        bigtiff=bigtiff,
    )
    print(f"已写出三维栈: {output}")
    print(f"  形状: {stack.shape}  (Z, Y, X" + (", C)" if stack.ndim == 4 else ")"))
    print(f"  类型: {stack.dtype}  大小约 {stack.nbytes / 1024**2:.1f} MiB")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="遍历子文件夹，把其中的二维 TIFF 叠成三维栈（ImageJ 可直接打开）",
    )
    parser.add_argument("input_dir", type=Path, help="包含多个子文件夹的根目录")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("stacked.tif"),
        help="输出三维 TIFF 路径（默认: ./stacked.tif）",
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
        "--dry-run",
        action="store_true",
        help="只列出将要叠入的文件和顺序，不写输出",
    )
    parser.add_argument(
        "--dtype",
        choices=("auto", *IMAGEJ_DTYPE_NAMES),
        default="auto",
        help="输出像素类型。auto（默认）会在 ImageJ 不支持原类型时自动转换",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tiffs = find_tiffs(args.input_dir.resolve(), recursive=args.recursive)
    if args.sort == "name":
        tiffs = sorted(tiffs, key=lambda p: natural_key(p.name))
    try:
        stack_and_write(
            tiffs,
            args.output.resolve(),
            dry_run=args.dry_run,
            dtype=args.dtype,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
