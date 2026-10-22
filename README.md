# 极简背单词机

> 把「认识/不认识」记进 SQLite，按遗忘曲线安排复习的桌面背单词工具。

## 它解决什么

背单词软件大多把「认识 / 不认识」做成一次性判断，结果第二天全忘。这个工具把每轮的判定结果写进 SQLite，按遗忘曲线决定哪些词该在今天出现。

## 关键实现

- 三层数据：词库 → 生词本 → 复习记录，判定结果直接决定下次出现时间
- 词典批量导入，一行一词的纯文本即可
- 单文件数据库，拷走 `.db` 就能换机继续

> 运行时会自动建库，仓库不附带词库数据。

## 技术栈

- **语言**：Python 3 + tkinter
- **存储**：SQLite（`db_manager.py` 封装建表与查询）
- **功能**：生词本分类标记、词典一键导入、按遗忘曲线安排复习

## 目录结构

```
  create_sample_dict.py
  db_manager.py
  main.py
  patch.py
  requirements.txt
```

## 快速开始

`pip install -r requirements.txt` 后 `python main.py`。

---

<sub>个人工程归档 · 2026 · MIT</sub>
