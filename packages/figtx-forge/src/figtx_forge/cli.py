"""figtx 命令行入口：只做参数解析和分发，逻辑都在各模块里。"""
from __future__ import annotations

import argparse
import sys
from typing import Callable

from . import __version__

# 子命令注册表：name -> (配置 parser 的函数, 处理函数)。各模块往这里加。
SUBCOMMANDS: dict[str, tuple[Callable, Callable]] = {}


def register(name: str):
    def deco(fn_pair: tuple[Callable, Callable]):
        SUBCOMMANDS[name] = fn_pair
        return fn_pair
    return deco


def _add_validate(p: argparse.ArgumentParser) -> None:
    p.add_argument("scene", help="场景 JSON 路径")


def _run_validate(args) -> int:
    from .scene import load_scene, validate_scene

    errs = validate_scene(load_scene(args.scene))
    for e in errs:
        print(e, file=sys.stderr)
    if not errs:
        print("ok")
    return 1 if errs else 0


SUBCOMMANDS["validate"] = (_add_validate, _run_validate)


def _load_plugins() -> None:
    """导入会注册子命令的模块（缺失的模块直接跳过，便于逐步开发）。"""
    import importlib

    for mod in ("commands",):
        try:
            importlib.import_module(f"figtx_forge.{mod}")
        except ModuleNotFoundError as e:
            if e.name != f"figtx_forge.{mod}":
                raise


def build_parser() -> argparse.ArgumentParser:
    _load_plugins()
    parser = argparse.ArgumentParser(prog="figtx", description="FigTX 工具包")
    parser.add_argument("--version", action="store_true", help="打印版本号")
    sub = parser.add_subparsers(dest="cmd")
    for name, (add, run) in SUBCOMMANDS.items():
        p = sub.add_parser(name)
        add(p)
        p.set_defaults(_run=run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if not getattr(args, "_run", None):
        build_parser().print_help()
        return 0
    return int(args._run(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
