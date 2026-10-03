"""金标测试脚本（设计文档 第六章·难点五、第八章·测试方法）。

读取 tests/golden_set/*.jsonl，逐条运行 RAG 链路，统计拒答正确率；
后续补充答案要点比对与出处正确率，并生成趋势曲线。
用法：python -m scripts.run_golden_test
"""
from __future__ import annotations

import json
from pathlib import Path

from app.intelligence import rag

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden_set"


def load_cases() -> list[dict]:
    cases: list[dict] = []
    for path in GOLDEN_DIR.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def main() -> None:
    cases = load_cases()
    if not cases:
        print("金标测试集为空，请先在 tests/golden_set 下补充问答对。")
        return

    correct = 0
    for case in cases:
        result = rag.answer(case["question"])
        refused = not hasattr(result, "matter_name")  # Refusal 或降级文本均视为未作答
        if case.get("should_refuse"):
            correct += int(refused)
        else:
            correct += int(not refused)

    print(f"用例数：{len(cases)}，正确：{correct}，准确率：{correct / len(cases):.1%}")
    # TODO 补充：答案要点比对、出处正确率统计、周度趋势曲线


if __name__ == "__main__":
    main()
