#!/usr/bin/env python3
"""台账统计与数据体检。

用法：
    python3 scripts/report.py           # 统计与诊断
    python3 scripts/report.py --check   # 只做数据体检
"""

from __future__ import annotations

import datetime
import sys
from collections import defaultdict

import common as c

REQUIRED = [
    "video_id", "publish_date", "platform", "track", "title",
    "form", "hook_type", "duration_sec", "shots", "cost_min", "notes",
]


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def is_filled(row: dict[str, str]) -> bool:
    v = str(row.get("rate_3s", "")).strip().upper()
    return bool(v) and v != "NA"


def bar(x: float, width: int = 12) -> str:
    n = max(0, min(width, int(round(x * width / 0.6))))
    return "█" * n + "·" * (width - n)


# ---------------------------------------------------------------- 体检

def do_check() -> int:
    problems: list[str] = []
    videos = c.read_rows(c.VIDEOS)
    tracks = c.read_rows(c.TRACKS)
    metrics = c.read_rows(c.METRICS)

    if not videos:
        problems.append("videos.csv 是空的")

    track_ids = {r.get("track_id", "") for r in tracks}
    seen: set[str] = set()

    for i, r in enumerate(videos, start=2):
        vid = r.get("video_id", "").strip()
        if not vid:
            problems.append(f"第 {i} 行：video_id 为空")
        elif vid in seen:
            problems.append(f"第 {i} 行：video_id 重复 → {vid}")
        seen.add(vid)

        for col in REQUIRED:
            if not str(r.get(col, "")).strip():
                problems.append(f"{vid or f'第{i}行'}：必填字段 {col} 为空")

        d = r.get("publish_date", "").strip()
        if d:
            try:
                datetime.date.fromisoformat(d)
            except ValueError:
                problems.append(f"{vid}：publish_date 格式错误 → {d}")

        t = r.get("track", "").strip()
        if t and track_ids and t not in track_ids:
            problems.append(f"{vid}：赛道 {t} 不在 tracks.csv 里")

        for col in ("rate_3s", "rate_complete"):
            raw = str(r.get(col, "")).strip().upper()
            if raw and raw != "NA":
                v = c.num(raw, -1)
                if not (0 <= v <= 1):
                    problems.append(f"{vid}：{col} 应在 0-1 之间 → {raw}（是不是填成了百分数？）")

        if str(r.get("notes", "")).strip() in ("", "数据待回填"):
            continue

    for r in metrics:
        vid = r.get("video_id", "")
        if vid and vid not in seen:
            problems.append(f"metrics.csv：{vid} 在 videos.csv 中不存在")

    print("\n=== 数据体检 ===")
    print(f"videos.csv：{len(videos)} 条　tracks.csv：{len(tracks)} 条　metrics.csv：{len(metrics)} 条\n")

    if not problems:
        print("没有发现问题。\n")
        return 0

    print(f"发现 {len(problems)} 个问题：\n")
    for p in problems:
        print(f"  · {p}")
    print()
    return 1


# ---------------------------------------------------------------- 统计

def group_stats(rows: list[dict[str, str]], key: str) -> list[tuple]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        if is_filled(r):
            buckets[r.get(key, "?") or "?"].append(r)

    out = []
    for name, items in buckets.items():
        n = len(items)
        a3 = sum(c.num(r.get("rate_3s")) for r in items) / n
        ac = sum(c.num(r.get("rate_complete")) for r in items) / n
        decay = ac / a3 if a3 else 0
        views = sum(c.num(r.get("views_72h")) for r in items) / n
        out.append((name, n, a3, ac, decay, views))
    out.sort(key=lambda x: -x[2])
    return out


def do_report() -> None:
    videos = c.read_rows(c.VIDEOS)
    if not videos:
        print("台账还是空的。先运行 python3 scripts/new_video.py 登记第一条。")
        return

    filled = [r for r in videos if is_filled(r)]
    print("\n=== AI 短视频台账统计 ===\n")
    print(f"总条数：{len(videos)}　已回填数据：{len(filled)}　待回填：{len(videos) - len(filled)}")

    if not filled:
        print("\n还没有可分析的数据。72 小时后回填 views_72h / rate_3s / rate_complete 再来。\n")
        return

    a3 = sum(c.num(r.get("rate_3s")) for r in filled) / len(filled)
    ac = sum(c.num(r.get("rate_complete")) for r in filled) / len(filled)
    decay = ac / a3 if a3 else 0
    total_cost = sum(c.num(r.get("cost_min")) for r in videos)

    print(f"\n平均 3 秒完播率：{pct(a3)}")
    print(f"平均完播率　　：{pct(ac)}")
    print(f"平均衰减比　　：{decay:.2f}　（完播率 ÷ 3秒完播率）")
    print(f"累计人工耗时　：{total_cost / 60:.1f} 小时　（单条均 {total_cost / len(videos) / 60:.1f} 小时）")

    # 钩子类型
    print("\n--- 按钩子类型 ---")
    print(f"{'钩子':<10}{'条数':>5}{'3秒完播':>10}{'完播率':>10}{'衰减比':>9}　分布")
    print("-" * 62)
    for name, n, x3, xc, dc, _ in group_stats(filled, "hook_type"):
        print(f"{name:<10}{n:>5}{pct(x3):>10}{pct(xc):>10}{dc:>9.2f}　{bar(x3)}")

    # 赛道
    print("\n--- 按赛道 ---")
    print(f"{'赛道':<10}{'条数':>5}{'3秒完播':>10}{'完播率':>10}{'均播放':>10}")
    print("-" * 50)
    for name, n, x3, xc, dc, views in group_stats(filled, "track"):
        print(f"{name:<10}{n:>5}{pct(x3):>10}{pct(xc):>10}{views:>10.0f}")

    # 榜单
    ranked = sorted(filled, key=lambda r: -c.num(r.get("views_72h")))
    print("\n--- 播放 Top 3 ---")
    for r in ranked[:3]:
        print(f"  {c.num(r.get('views_72h')):>8.0f}  {r.get('video_id')}  "
              f"[{r.get('hook_type')}]  3s {pct(c.num(r.get('rate_3s')))}")
    if len(ranked) > 3:
        print("--- 播放 Bottom 3 ---")
        for r in ranked[-3:]:
            print(f"  {c.num(r.get('views_72h')):>8.0f}  {r.get('video_id')}  "
                  f"[{r.get('hook_type')}]  3s {pct(c.num(r.get('rate_3s')))}")

    # 诊断
    print("\n--- 诊断 ---")
    tips = []
    if a3 < 0.30:
        tips.append("平均 3 秒完播率低于 30%：钩子普遍无效。前 3 秒删掉所有铺垫，只留冲突。")
    elif a3 < 0.40:
        tips.append("平均 3 秒完播率 30-40%：钩子及格但不够强，试试换 hook_type 做对照。")
    else:
        tips.append(f"平均 3 秒完播率 {pct(a3)}：钩子有效，可以把最强的结构复制 3 条。")

    if decay < 0.25:
        tips.append("衰减比低于 0.25：观众在某个位置集体划走。回看留存曲线找掉量秒数。")
    elif decay < 0.40:
        tips.append("衰减比 0.25-0.40：中段偏拖，压缩到每 8 秒一个信息点。")

    if len(filled) < 10:
        tips.append(f"样本只有 {len(filled)} 条，结论不可靠。攒到 10 条以上再看分组对比。")

    per_hook = group_stats(filled, "hook_type")
    if len(per_hook) >= 2 and per_hook[0][2] - per_hook[-1][2] > 0.10:
        tips.append(
            f"钩子差异明显：「{per_hook[0][0]}」{pct(per_hook[0][2])} vs "
            f"「{per_hook[-1][0]}」{pct(per_hook[-1][2])}，优先做前者。"
        )

    for t in tips:
        print(f"  · {t}")
    print()


def main() -> None:
    if "--check" in sys.argv:
        raise SystemExit(do_check())
    do_report()


if __name__ == "__main__":
    main()
