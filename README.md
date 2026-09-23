# notesdb

本地 Markdown 笔记库工具：frontmatter 存储、双链笔记、全文检索、查询语言、静态导出。

不引入数据库与外部服务——笔记库就是磁盘上的一目录 `.md` 文件，
任何编辑器都能直接改，notesdb 只提供"读得快、找得到、看得清"。

## 安装

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

依赖只有 PyYAML（标准库之外的全部自己写）。

## 快速开始

```bash
mkdir -p my-notes/notes && cd my-notes
python -m notesdb new 第一篇 --title "开始" --tag start   # 建笔记
python -m notesdb list                                     # 看库
python -m notesdb query 'tag:start'                        # 查询
python -m notesdb export                                   # 离线 HTML 导出
```

## 命令一览

**只读**

| 命令 | 作用 |
|---|---|
| `list` | 全部笔记（名/标题/标签） |
| `query '<串>'` | 查询（语法见下） |
| `tags` / `links` / `stats` / `report` | 标签统计 / 链接图 / 库统计 / Markdown 报表 |
| `export` | 静态站点导出到 `export/`（浏览器直接打开，完全离线） |
| `lint` | 库健康检查（坏 frontmatter/名字冲突是 error，悬空/孤岛/空笔记是 warning） |
| `walk [n] --seed s` | 随机漫游链接图（重新发现沉睡笔记） |
| `similar <名>` | 相似笔记推荐（Jaccard 词元重合） |
| `suggest <名>` | 链接建议 + 悬空链接模糊修复建议 |
| `today` | 今日每日笔记状态 |

**写入**

| 命令 | 作用 |
|---|---|
| `new <名> [--title] [--tag …]` | 新建笔记 |
| `rename <旧> <新>` | 改名并同步全库 `[[引用]]` |
| `delete <名>` | 删除（自动先备份） |
| `tag add\|remove <名> <标签>` | 标签增删 |
| `import <目录> [--mode skip\|suffix\|overwrite]` | 批量导入（保留子目录结构） |
| `backup [--keep n]` / `backups` / `restore <zip>` | 备份家族 |

## 查询语法

```
词1 词2            全文检索（AND）
tag:work -tag:tmp  标签包含/排除
"精确短语"          短语检索（保序）
link:目标           引用了某笔记
orphan / unresolved 只看孤岛 / 带悬空链接
```

中英混合自动适配：英文按词、中文按 bigram，检索与建索引同口径。

## 笔记格式

```markdown
---
title: 标题（可选）
tags: [work, project]      # 列表或逗号串都行
---
正文，支持 [[双链]]、[[目标|别名]]、{{frontmatter变量}}、{{today}}。

代码块里的 [[x]] 不算链接。
```

每篇笔记一个 `.md` 文件，文件名即笔记名；`sub/page.md` → 笔记名
`sub/page`（分层名）。

## 配置

库根放 `notesdb.json`（全部可选）：

```json
{
  "index_threshold": 0.2,
  "backup_keep": 10,
  "exclude": ["draft-*", "private/*"]
}
```

环境变量 `NDB_<键名>` 再覆盖一层。未知键/坏 JSON 直接报错——
静默忽略拼错的配置是最坑用户的行为。

## 开发

```bash
python -m pip install -r requirements-dev.txt
python -m pytest          # 280+ 测试，不依赖网络
ruff check .              # 代码规范
```

架构：`notesdb/` 每模块一个职责（模型/存储/链接图/索引/标签/查询/
渲染/导出/编辑/备份/导入/建议/漫游…），`tests/` 逐模块回归 +
CLI 端到端（真子进程）。变更记录见 `CHANGELOG.md`。

## 免责声明

笔记内容不经任何外部服务（索引/导出全本地）。
