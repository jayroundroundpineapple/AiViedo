# scripts · 工具脚本

只依赖 Python 3.8+ 标准库，**不需要 pip install 任何东西**。

## 三个脚本

### `track_score.py` — 赛道六维打分

```bash
python3 scripts/track_score.py          # 交互式打分
python3 scripts/track_score.py --list   # 查看已有赛道
```

输入六个 0-10 分，脚本按权重算出总分，给出「立项 / 观察 / 放弃」结论，并写入 `data/tracks.csv`。

权重：变现距离 0.25、需求热度 0.20、竞争强度 0.20（反向）、可持续性 0.15、资源匹配 0.15、合规风险 0.05（反向）。

详见 [`../docs/03-赛道评估模型.md`](../docs/03-赛道评估模型.md)。

### `new_video.py` — 登记视频

```bash
python3 scripts/new_video.py                 # 交互式
python3 scripts/new_video.py --import f.csv  # 批量导入
```

自动生成 `video_id`（`YYYYMMDD-平台-序号`），数据字段先填 `NA`，72 小时后回填。

导入模式会跳过重复的 `video_id`，不会覆盖已有数据。

### `report.py` — 统计与体检

```bash
python3 scripts/report.py           # 统计与诊断
python3 scripts/report.py --check   # 只做数据体检
```

输出：平均 3 秒完播率、完播率、衰减比、按钩子/赛道分组对比、播放 Top3、自动诊断建议。

`--check` 会检查：必填字段缺失、`video_id` 重复、比率超出 0-1、日期格式、赛道不存在、快照孤儿行。

## `common.py`

共用工具：路径常量、CSV 读写（自动兼容 Excel 的 BOM）、数值解析（`NA` / `42%` / 空值都能吃）、交互输入。

## 常见问题

**Q：Excel 打开 CSV 中文乱码？**
A：脚本读的是 `utf-8-sig`，能兼容 BOM。如果你用 Excel 另存过，可能会变成 GBK——用 VSCode 重新存成 UTF-8 即可。

**Q：能不能加爬虫自动抓抖音数据？**
A：不做。平台条款普遍禁止自动化采集，且涉及个人信息。详见 [`../docs/02-合规红线.md`](../docs/02-合规红线.md)。数据来源应该是平台创作者后台的官方导出。

**Q：报 `ModuleNotFoundError: common`？**
A：在仓库根目录运行 `python3 scripts/xxx.py`，不要在 `scripts/` 目录里直接跑。
