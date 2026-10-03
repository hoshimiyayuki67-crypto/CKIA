"""知识库入库脚本（设计文档 第七章·知识库建设）。

流程：收集文档 -> 解析 -> 清洗切分 -> 附加元数据 -> 向量化 -> 写入向量库。
用法：python -m scripts.ingest
"""
from __future__ import annotations

from app.data import doc_store, vector_store
from app.intelligence import embedding


def main() -> None:
    chunks = doc_store.load_documents()
    if not chunks:
        print("未发现待入库文档，请将校内公开文档放入 app/data/knowledge/{official,experience}/。")
        return

    vectors = embedding.embed([c.chunk_text for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk.vector = vector
    vector_store.add(chunks)
    print(f"入库完成，共 {len(chunks)} 个片段。")


if __name__ == "__main__":
    main()
