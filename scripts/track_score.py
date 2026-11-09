#!/usr/bin/env python3
"""赛道六维打分。

用法：
    python3 scripts/track_score.py            # 交互式打分
    python3 scripts/track_score.py --list     # 查看已有赛道

打分规则见 docs/03-赛道评估模型.md
"""

from __future__ import annotations

import sys

import common as c

WEIGHTS = {
    "need": 0.20,      # 需求热度（正）
    "comp": 0.20,      # 竞争强度（反）
    "money": 0.25,     # 变现距离（正）
    "durable": 0.15,   # 可持续性（正）
    "fit": 0.15,       # 资源匹配（正）
    "risk": 0.05,      # 合规风险（反）
}

NEGATIVE = {"comp", "risk"}


def compute(scores: dict[str, float]) -> float:
    total = 0.0
    for key, w in WEIGHTS.items():
        s = scores[key]
        if key in NEGATIVE:
            s = 10 - s
        total += w * s
    return round(total, 2)


def verdict(total: float) -> tuple[str, str]:
    if total >= 7.5:
        return "立项", "立刻做 3 条测试片"
    if total >= 7.0:
        return "立项（观察）", "先做 1 条试水，看 3 秒完播率"
    if total >= 6.0:
        return "观察", "不投入生产，先持续收集该赛道爆款"
    return "放弃", "记录原因，不再回头看"


def show_list() -> None:
    rows = c.read_rows(c.TRACKS)
    if not rows:
        print("赛道库还是空的。运行 python3 scripts/track_score.py 添加第一个。")
        return

    print(f"\n{'ID':<5}{'赛道':<24}{'状态':<11}{'总分':<7}{'结论':<14}理由")
    print("-" * 96)
    for r in rows:
        name = r.get("name", "")[:22]
        print(
            f"{r.get('track_id',''):<5}{name:<24}{r.get('status',''):<11}"
            f"{r.get('total',''):<7}{r.get('verdict',''):<14}{r.get('reason','')[:34]}"
        )
    print()


def next_id(rows: list[dict[str, str]]) -> str:
    used = {r.get("track_id", "") for r in rows}
    for i in range(1, 100):
        tid = f"T{i:02d}"
        if tid not in used:
            return tid
    c.fail("赛道编号已用满 99 个")


def main() -> None:
    if "--list" in sys.argv or "-l" in sys.argv:
        show_list()
        return

    rows = c.read_rows(c.TRACKS)

    print("\n=== 赛道六维打分 ===")
    print("每个维度 0-10 分。竞争强度与合规风险是反向指标（分越高越差）。\n")

    name = c.ask("赛道名称（如：跨境电商母婴用品）")
    platform = c.ask("主要平台", "dy", c.PLATFORMS)

    print("\n--- 六个维度 ---")
    print("需求热度：这个内容有人主动搜吗？")
    need = c.ask_score("  需求热度")
    print("竞争强度：头部是否已固化？分越高越难做")
    comp = c.ask_score("  竞争强度")
    print("变现距离：从内容到收钱要几步？")
    money = c.ask_score("  变现距离")
    print("可持续性：这个题材能做满 100 条吗？")
    durable = c.ask_score("  可持续性")
    print("资源匹配：你有没有别人没有的优势？")
    fit = c.ask_score("  资源匹配")
    print("合规风险：有没有肖像/医疗/金融/版权硬伤？分越高越危险")
    risk = c.ask_score("  合规风险")

    scores = {
        "need": need, "comp": comp, "money": money,
        "durable": durable, "fit": fit, "risk": risk,
    }
    total = compute(scores)
    v, action = verdict(total)

    print("\n--- 计算过程 ---")
    for key, w in WEIGHTS.items():
        s = scores[key]
        eff = 10 - s if key in NEGATIVE else s
        tag = "（反向已翻转）" if key in NEGATIVE else ""
        print(f"  {key:<8} {s:>4.0f} × {w:.2f} = {w * eff:>5.2f}  {tag}")
    print(f"\n  总分：{total}  →  {v}")
    print(f"  建议：{action}\n")

    if total < 6.0:
        print("  提醒：总分低于 6 分。除非你有明确的非量化理由，否则不要开做。")

    reason = c.ask("一句话判断依据（会写进台账）", f"{name}：{v}")
    tid = next_id(rows)
    status = "active" if total >= 7.0 else ("candidate" if total >= 6.0 else "dropped")

    c.append_rows(c.TRACKS, [{
        "track_id": tid,
        "name": name,
        "platform": platform,
        "status": status,
        "score_need": f"{need:.0f}",
        "score_comp": f"{comp:.0f}",
        "score_money": f"{money:.0f}",
        "score_durable": f"{durable:.0f}",
        "score_fit": f"{fit:.0f}",
        "score_risk": f"{risk:.0f}",
        "total": total,
        "verdict": v,
        "reason": reason,
    }])

    print(f"\n已写入 data/tracks.csv：{tid} {name}（{v}）")


if __name__ == "__main__":
    main()
