"""公共工具：路径、CSV 读写、数值解析。

只依赖 Python 3 标准库，无第三方依赖。
"""

from __future__ import annotations

import csv
import os
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

VIDEOS = os.path.join(DATA, "videos.csv")
TRACKS = os.path.join(DATA, "tracks.csv")
METRICS = os.path.join(DATA, "metrics.csv")

PLATFORMS = ["dy", "xhs", "bl", "sph", "yt", "tt"]
FORMS = ["ai_full", "digital_human", "ai_assisted"]
HOOKS = ["反常识", "结果前置", "冲突", "痛点", "悬念", "对比"]


def read_rows(path: str) -> list[dict[str, str]]:
    """读取 CSV，自动兼容 BOM（Excel 导出的常见问题）。"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def header(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f), [])


def append_rows(path: str, rows: list[dict[str, Any]]) -> None:
    """追加写入，缺列补空，多列忽略，保证与表头一致。"""
    if not rows:
        return
    cols = header(path)
    if not cols:
        raise SystemExit(f"找不到表头：{path}")

    need_newline = False
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            need_newline = f.read(1) != b"\n"

    with open(path, "a", encoding="utf-8", newline="") as f:
        if need_newline:
            f.write("\n")
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def num(value: Any, default: float = 0.0) -> float:
    """把 '0.42' / '42%' / 'NA' / '' 统一转成 float。"""
    if value is None:
        return default
    s = str(value).strip()
    if not s or s.upper() == "NA":
        return default
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100
        except ValueError:
            return default
    try:
        return float(s)
    except ValueError:
        return default


def ask(prompt: str, default: str = "", choices: list[str] | None = None) -> str:
    """交互输入，支持默认值与枚举校验。"""
    suffix = f" [{default}]" if default else ""
    if choices:
        suffix = f" ({'/'.join(choices)}){suffix}"
    while True:
        val = input(f"{prompt}{suffix}: ").strip()
        if not val:
            if default:
                return default
            print("  这一项不能为空，请重新输入。")
            continue
        if choices and val not in choices:
            print(f"  只能是：{'/'.join(choices)}")
            continue
        return val


def ask_score(prompt: str) -> float:
    """0-10 分输入，带范围校验。"""
    while True:
        raw = input(f"{prompt} (0-10): ").strip()
        try:
            v = float(raw)
        except ValueError:
            print("  请输入数字。")
            continue
        if 0 <= v <= 10:
            return v
        print("  范围是 0-10。")


def ask_float(prompt: str, default: float = 0.0) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    return num(raw, default)


def ask_int(prompt: str, default: int = 0) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    return int(num(raw, float(default)))


def fail(msg: str) -> None:
    print(f"错误：{msg}", file=sys.stderr)
    raise SystemExit(1)
