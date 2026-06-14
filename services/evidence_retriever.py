"""
古籍证据检索服务 (Phase A1)

职责：
  - 暴露 fetch_evidence(keywords, top_k) 单一入口
  - 将关键词列表合并为查询串，调用 tfidf_score() 排序
  - 返回 top_k 条古籍片段（id / title / passage / score）

设计约束：
  - 仅依赖 services.classics_search，不导入任何 routers/ 模块（避免 F1 循环导入）
  - 所有数据来自内存缓存，不访问 DB / 外部网络
"""

from __future__ import annotations

import logging

from services.classics_search import load_classics, tfidf_score

logger = logging.getLogger(__name__)

# 返回的单条证据结构（轻量 dict，不使用 Pydantic 以减少开销）
# keys: id, title, passage, score
_PASSAGE_PREVIEW_LEN = 200  # 最多截取多少字送入 LLM


def fetch_evidence(
    keywords: list[str],
    top_k: int = 3,
) -> list[dict]:
    """
    根据关键词列表检索相关古籍片段，返回相关度最高的 top_k 条。

    参数
    ----
    keywords : 关键词列表，如 ["事业", "官星", "正官", "七杀"]
    top_k    : 返回条数，默认 3

    返回
    ----
    list[dict]，每条包含:
      id      : 古籍 ID（如 "CLS001"）
      title   : 书名（如 "子平真诠"）
      passage : 原文片段（截取前 200 字）
      score   : TF-IDF 相关度得分（float）

    若古籍库为空或无关键词，返回空列表。
    """
    if not keywords:
        return []

    docs = load_classics()
    if not docs:
        logger.warning("fetch_evidence: classics library is empty")
        return []

    # 构造检索文本对列表：(用于评分的文本, 原文档对象)
    text_obj_pairs = [
        (
            f"{doc.title} {doc.passage} {doc.notes or ''} {' '.join(doc.tags)}",
            doc,
        )
        for doc in docs
    ]

    query = " ".join(keywords)
    scored = tfidf_score(query, text_obj_pairs)

    results: list[dict] = []
    for score, doc in scored[:top_k]:
        if score <= 0.0:
            break
        results.append(
            {
                "id": doc.id,
                "title": doc.title,
                "passage": doc.passage[:_PASSAGE_PREVIEW_LEN],
                "score": round(score, 4),
            }
        )

    logger.debug(
        "fetch_evidence: query=%r, hits=%d/%d",
        query[:60],
        len(results),
        len(docs),
    )
    return results
