---
name: simplify
description: 執行程式碼簡化任務
allowed_tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
---

執行程式碼簡化任務。使用 code-simplifier agent 來分析和簡化指定的檔案。

用法：
- `/simplify src/services/notion_service.py` - 簡化指定檔案
- `/simplify --all` - 分析整個 src/ 目錄
- `/simplify --constants` - 只提取常數

## 簡化流程

1. **分析檔案** - 識別可簡化的區域
2. **建立快照** - 確保可回滾
3. **執行簡化** - 逐步修改
4. **驗證** - 確認功能不變

## 簡化技術

- 提取 magic numbers 為常數
- 減少巢狀條件
- 消除重複程式碼
- 改善命名一致性
- 移除死碼
