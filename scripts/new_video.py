#!/usr/bin/env python3
"""登记一条已发布的视频。

用法：
    python3 scripts/new_video.py                 # 交互式登记
    python3 scripts/new_video.py --import f.csv  # 从 CSV 批量导入

字段定义见 docs/01-数据规范.md
"""

from __future__ import annotations

import datetime
import os
import sys

import common as c


def existing_seq(rows: list[dict[str, str]], date: str, platform: str) -> int:
    """找出该日期该平台已用的最大序号。"""
    prefix = f"{date.replace('-', '')}-{platform}-"
    max_seq = 0
    for r in rows:
        vid = r.get("video_id", "")
        if vid.startswith(prefix):
            try:
                max_seq = max(max_seq, int(vid[len(prefix):]))
            except ValueError:
                continue
    return max_seq


def do_import(path: str) -> None:
    if not os.path.exists(path):
        c.fail(f"文件不存在：{path}")

    src = c.read_rows(path)
    if not src:
        c.fail("文件是空的，或者没有表头")

    cols = c.header(c.VIDEOS)
    missing = [x for x in ("video_id", "publish_date", "platform") if x not in src[0]]
    if missing:
        c.fail(f"缺少必需列：{', '.join(missing)}")

    seen = {r.get("video_id", "") for r in c.read_rows(c.VIDEOS)}
    added, skipped = [], []
    for r in src:
        vid = r.get("video_id", "").strip()
        if not vid:
            skipped.append("（空 video_id）")
            continue
        if vid in seen:
            skipped.append(vid)
            continue
        seen.add(vid)
        added.append({k: r.get(k, "") for k in cols})

    c.append_rows(c.VIDEOS, added)
    print(f"已导入 {len(added)} 条。")
    if skipped:
        print(f"跳过 {len(skipped)} 条（重复或缺少主键）：{', '.join(skipped[:10])}")


def do_interactive() -> None:
    rows = c.read_rows(c.VIDEOS)
    tracks = c.read_rows(c.TRACKS)
    track_ids = [r.get("track_id", "") for r in tracks if r.get("track_id")]

    print("\n=== 登记一条视频 ===\n")

    date = c.ask("发布日期 YYYY-MM-DD", datetime.date.today().isoformat())
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        c.fail("日期格式不对，应该是 2026-11-09 这样")

    platform = c.ask("平台", "dy", c.PLATFORMS)

    if track_ids:
        print(f"  已有赛道：{', '.join(track_ids)}")
    track = c.ask("赛道代码", track_ids[0] if track_ids else "T01")

    title = c.ask("完整标题（含话题标签）")
    form = c.ask("形态", "ai_assisted", c.FORMS)
    hook = c.ask("钩子类型", "反常识", c.HOOKS)

    print("\n--- 生产信息 ---")
    duration = c.ask_int("时长（秒）", 60)
    shots = c.ask_int("镜头数", 8)
    cost = c.ask_int("总人工耗时（分钟）", 240)

    seq = existing_seq(rows, date, platform) + 1
    vid = f"{date.replace('-', '')}-{platform}-{seq:02d}"

    print(f"\n--- 自动生成 video_id：{vid} ---")
    print("  数据字段先填 NA，72 小时后用同样的 video_id 回填。\n")

    c.append_rows(c.VIDEOS, [{
        "video_id": vid,
        "publish_date": date,
        "platform": platform,
        "track": track,
        "title": title,
        "form": form,
        "hook_type": hook,
        "duration_sec": duration,
        "shots": shots,
        "cost_min": cost,
        "views_72h": "NA",
        "rate_3s": "NA",
        "rate_complete": "NA",
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "saves": 0,
        "follows": 0,
        "gmv": 0,
        "notes": "数据待回填",
    }])

    print(f"已写入 data/videos.csv：{vid}")
    print(f"成片文件请重命名为：{vid}.mp4")
    print(f"72 小时后回填数据，并在 notes 写一句话结论。")


def main() -> None:
    if "--import" in sys.argv:
        i = sys.argv.index("--import")
        if i + 1 >= len(sys.argv):
            c.fail("用法：python3 scripts/new_video.py --import 文件.csv")
        do_import(sys.argv[i + 1])
        return
    do_interactive()


if __name__ == "__main__":
    main()
