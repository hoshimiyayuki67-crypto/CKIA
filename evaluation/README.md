# 金标评测准备

golden/ 存人工审核的 JSONL；reports/ 存评测结果。当前不生成虚构的 100 条“金标”。每条字段：id、question、category、expected_status、answer_points、source_doc_ids、source_chunk_ids、scenario。

覆盖标准/口语提问、澄清、无关问题、旧通知、冲突信息、模糊截图。至少 100 条，覆盖六大类与 ≥15 项事务；每周评测并记录数据集版本、模型/提示词版本、阈值、耗时及错误样例。
