from functools import wraps
import hashlib
import json
import logging
from typing import Any, Callable, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 轻量级内存字典（后续可扩展对接 Redis）
_LRU_CACHE = {}
_MAX_CACHE_SIZE = 1000

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """生成请求签名 Hash"""
    # 提取所有 Pydantic 模型作为 dict，其余转 string
    serializable = []
    for arg in args:
        if isinstance(arg, BaseModel):
            serializable.append(arg.model_dump())
        else:
            serializable.append(str(arg))
    for k, v in kwargs.items():
        if isinstance(v, BaseModel):
            serializable.append(f"{k}:{v.model_dump()}")
        else:
            serializable.append(f"{k}:{str(v)}")

    canonical_str = json.dumps(serializable, sort_keys=True)
    digest = hashlib.md5(canonical_str.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"

def api_response_cache(prefix: str = "ziwei_full"):
    """
    API 响应缓存装饰器：
    用于缓解大运算量 API 的 CPU 压力。相同输入直接返回。
    """
    def decorator(func: Callable):
        if getattr(func, "_is_coroutine", False) or __import__("inspect").iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = get_cache_key(prefix, *args, **kwargs)
                if key in _LRU_CACHE:
                    logger.debug(f"API Cache HIT: {key}")
                    return _LRU_CACHE[key]
                
                result = await func(*args, **kwargs)
                
                if len(_LRU_CACHE) > _MAX_CACHE_SIZE:
                    # 简单剔除第一个 (非 LRU，仅防 OOM)
                    _LRU_CACHE.pop(next(iter(_LRU_CACHE)))
                
                _LRU_CACHE[key] = result
                logger.debug(f"API Cache SET: {key}")
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = get_cache_key(prefix, *args, **kwargs)
                if key in _LRU_CACHE:
                    logger.debug(f"API Cache HIT: {key}")
                    return _LRU_CACHE[key]
                
                result = func(*args, **kwargs)
                if len(_LRU_CACHE) > _MAX_CACHE_SIZE:
                    _LRU_CACHE.pop(next(iter(_LRU_CACHE)))
                _LRU_CACHE[key] = result
                logger.debug(f"API Cache SET: {key}")
                return result
            return sync_wrapper
    return decorator

