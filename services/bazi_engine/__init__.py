"""
services/bazi_engine — 八字命理计算引擎包（v7.0）

包结构（按依赖层级）：
  第0层 — 基础数据（无任何依赖）
    tables.py           11张查找表 + self_check()
    solar_time_v2.py    Spencer EoT 公式
    classic_refs.py     静态古籍引用数据
    lifestyle/tables.py 五行→生活建议映射表

  第1层 — 核心计算（仅依赖第0层）
    wuxing.py / shensha.py / geju.py / palace.py / liunian.py

  第2层 — 推导计算
    strength.py / dayun.py

  第3层 — 决策计算
    yongshen.py

  第4层 — 分析引擎（analysis/ 子包）
    wealth / career / marriage / health / relationship / personality / monthly

  第5层 — 集成与解读
    interpret.py / life_arc.py / milestones.py / lifestyle/

  第6层 — 服务入口
    bazi_engine_service.py::calculate()

O11: 统一 re-export，各 router 可使用
    from services.bazi_engine import compute_geju, compute_monthly, ...
"""
from __future__ import annotations

# 第1层
from .geju import compute_geju
from .wuxing import compute_wuxing, compute_shishen_scores
from .shensha import compute_shensha
from .palace import compute_palace
from .liunian import compute_liunian

# 第2层
from .strength import compute_strength
from .dayun import compute_dayun

# 第3层
from .yongshen import compute_yongshen

# 第4层 — 分析引擎
from .analysis.monthly import compute_monthly
from .analysis.liunian_domain import compute_liunian_domain_forecasts
from .analysis.dayun_narrative import generate_dayun_narrative
from .analysis.wealth import compute_wealth
from .analysis.career import compute_career
from .analysis.marriage import compute_marriage
from .analysis.health import compute_health
from .analysis.personality import compute_personality

# 第5层 — lifestyle
from .lifestyle.lucky import compute_lucky
from .lifestyle.fengshui import compute_fengshui
from .lifestyle.jewelry import compute_jewelry
from .lifestyle.lifestyle import compute_lifestyle

__all__ = [
    # 第1层
    "compute_geju",
    "compute_wuxing",
    "compute_shishen_scores",
    "compute_shensha",
    "compute_palace",
    "compute_liunian",
    # 第2层
    "compute_strength",
    "compute_dayun",
    # 第3层
    "compute_yongshen",
    # 第4层
    "compute_monthly",
    "compute_liunian_domain_forecasts",
    "generate_dayun_narrative",
    "compute_wealth",
    "compute_career",
    "compute_marriage",
    "compute_health",
    "compute_personality",
    # 第5层
    "compute_lucky",
    "compute_fengshui",
    "compute_jewelry",
    "compute_lifestyle",
]

