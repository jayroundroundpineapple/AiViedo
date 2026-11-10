# data · 数据台账

> 这个目录是整个仓库最值钱的部分。三个月后你唯一能相信的就是这里的数字。

## 文件说明

| 文件 | 作用 | 谁写入 |
|---|---|---|
| `tracks.csv` | 赛道库，记录候选/在跑/放弃的赛道及打分 | `scripts/track_score.py` 或手工 |
| `videos.csv` | **核心表**，每条发布过的视频一行 | `scripts/new_video.py` 或手工 |
| `notes.csv` | 图文笔记台账，每条图文一行（点击率/收藏率/搜索占比） | 手工 |
| `episodes.csv` | 剧集台账，麻薯×大吉 25 集的选题、钩子、公式、状态 | 手工 |
| `metrics.csv` | 同一条视频在不同时点的数据快照 | 手工回填 |
| `raw/` | 平台导出的原始文件（不入库） | 手工放置 |

字段完整定义见 [`../docs/01-数据规范.md`](../docs/01-数据规范.md)。

### episodes.csv 字段

剧集台账只有 13 列，用来回答一个问题：**这 25 集排到哪一步了。**

| 字段 | 说明 |
|---|---|
| `ep_id` / `ep_no` | `E01`–`E25`，与 `docs/13` 的集号一致 |
| `title` / `one_line` | 集名与一句话剧情 |
| `hook_type` | 悬念式 / 反差式 / 日常式 / 情绪式（开头 3 秒的钩子类型） |
| `formula` | 套的是六条剧情公式中的哪一条 |
| `duration_sec` / `shots` | 目标时长与镜头数，用于估成本 |
| `status` | `pool` 选题池 → `script_ready` 有分镜 → `shot` 已出镜头 → `published` 已发布 → `dropped` 放弃 |
| `video_id` | 发布后填 `videos.csv` 的主键，两表靠它关联 |
| `publish_date` / `gmv` | 发布日与直接带来的成交额（视频本身不带货就填 0） |

**发布一条就回填一行**，`status` 从 `script_ready` 改成 `published` 并补上 `video_id`。这样"拍了多少、废了多少、哪条公式最能涨粉"三件事都能直接数出来。

## 示例数据说明

三个 CSV 里都带了 `示例` 开头的行，用来演示格式。**开始正式使用前请删掉示例行**，否则统计会被污染。

## 添加数据的三种方式

### 1. 交互式登记（推荐）

```bash
python3 scripts/new_video.py
```

会逐项询问字段，自动生成 `video_id` 并追加到 `videos.csv`。

### 2. 批量导入

把平台后台导出的表格整理成与 `videos.csv` 相同的列顺序，然后：

```bash
python3 scripts/new_video.py --import 你的文件.csv
```

### 3. 直接编辑

用 Excel / Numbers / VSCode 打开 CSV 手工加行。注意：

- 标题里含逗号时要用英文引号包起来：`"标题，含逗号"`
- 保存为 **UTF-8 编码**，不要用 Excel 默认的 GBK
- 数字列不要留空，没有就填 `0`

## 关于原始数据

`raw/` 已被 `.gitignore` 排除。平台导出的原始文件往往含个人信息和大量冗余字段，**不入库是正确的**——入库的应该只有你整理后的结构化字段。

如果确实需要保留原始文件，请放在网盘并在 `raw/README.md` 里记录位置，不要提交到 git。

## 数据健康检查

```bash
python3 scripts/report.py --check
```

会检查：字段缺失、`video_id` 重复、比率超出 0-1 范围、日期格式错误。
