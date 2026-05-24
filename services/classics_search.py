"""
古籍语料检索服务 (Phase A0 — F1 修复 + F3 bigram 增强)

职责：
  - 加载 data/classics.json 至内存（单例缓存）
  - 提供 tokenize() — 字符分词 + bigram 扩展
  - 提供 tfidf_score() — TF-IDF 相关度排序
  - 定义 ClassicPassageModel（从 routers/static_data 提取，避免循环导入）

供以下模块引用（不得反向依赖 routers/）：
  services/evidence_retriever.py
  routers/static_data.py（导入本模块函数代替原本地私有函数）
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
import logging
import math
from pathlib import Path
import re
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── 模型 ────────────────────────────────────────────────────────────────────

class ClassicPassageModel(BaseModel):
    id: str
    title: str
    author: str
    dynasty: str
    tags: list[str]
    passage: str
    notes: Optional[str] = None
    score: Optional[float] = None   # TF-IDF 相关度（仅搜索时返回）


# ── 加载（单例 + lru_cache）──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_classics() -> list[ClassicPassageModel]:
    """服务启动后一次性加载 data/classics.json 至内存，后续调用直接复用缓存。"""
    path = _DATA_DIR / "classics.json"
    if not path.exists():
        logger.warning("classics.json not found at %s", path)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = [ClassicPassageModel(**item) for item in raw]
        logger.info("Loaded %d classic passages from %s", len(items), path)
        return items
    except Exception as exc:
        logger.error("Failed to load classics.json: %s", exc)
        return []


# ── 分词（F3 修复：新增 bigram）──────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """
    中文 token 化：返回字符级 token + 相邻字符对（bigram）。

    示例：
      "七杀格" → ["七", "杀", "格", "七杀", "杀格"]

    与原字符级分词相比，bigram 大幅提升两字术语（如"官星"、"大运"）的召回率。
    """
    text_clean = re.sub(r"\s+", "", text)
    chars = [c for c in text_clean if c.strip()]
    bigrams = [text_clean[i: i + 2] for i in range(len(text_clean) - 1)
               if text_clean[i].strip() and text_clean[i + 1].strip()]
    return chars + bigrams


# ── TF-IDF 评分 ──────────────────────────────────────────────────────────────

def tfidf_score(
    query: str,
    documents: list[tuple[str, Any]],
) -> list[tuple[float, Any]]:
    """
    对文档列表计算 TF-IDF 相关度。

    参数
    ----
    query     : 检索关键词字符串
    documents : [(text, obj), ...]  其中 text 为用于检索的文本，obj 任意

    返回
    ----
    [(score, obj), ...] 按 score **降序**排列
    """
    query_terms = tokenize(query)
    if not query_terms:
        return [(0.0, obj) for _, obj in documents]

    N = len(documents)
    df: Counter[str] = Counter()
    tokenized_docs: list[list[str]] = []
    for text, _ in documents:
        tokens = tokenize(text)
        tokenized_docs.append(tokens)
        for t in set(tokens):
            df[t] += 1

    scores: list[tuple[float, Any]] = []
    for tokens, (_, obj) in zip(tokenized_docs, documents):
        tf_counter = Counter(tokens)
        doc_len = max(len(tokens), 1)
        score = 0.0
        for term in query_terms:
            tf = tf_counter.get(term, 0) / doc_len
            idf = math.log((N + 1) / (df.get(term, 0) + 1)) + 1.0
            score += tf * idf
        scores.append((score, obj))

    scores.sort(key=lambda x: -x[0])
    return scores
