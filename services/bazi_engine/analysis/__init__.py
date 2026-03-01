"""analysis — 分析引擎子包

各模块（M2 阶段逐步实现）：
  wealth.py           财运引擎 → WealthAnalysisModel
  career.py           事业引擎 → CareerAnalysisModel
  marriage.py         婚姻引擎 → MarriageAnalysisModel
  health.py           健康引擎 → HealthAnalysisModel
  relationship.py     人际引擎 → RelationshipAnalysisModel
  personality.py      性格引擎 → PersonalityModel
  monthly.py          月运引擎 → list[MonthlyFortuneModel]
  dayun_narrative.py  大运叙事 → str (M3)
  wealth_estimate.py  财富估算 → WealthEstimate (M3)
  liunian_domain.py   流年四维 → dict (M3 §4.11-H)

约束：同层模块互不调用，禁止循环依赖（见开发5.0.txt §4.12）。
"""

from services.bazi_engine.analysis.wealth import compute_wealth
from services.bazi_engine.analysis.career import compute_career
from services.bazi_engine.analysis.marriage import compute_marriage
from services.bazi_engine.analysis.health import compute_health
from services.bazi_engine.analysis.relationship import compute_relationship
from services.bazi_engine.analysis.personality import compute_personality
from services.bazi_engine.analysis.monthly import compute_monthly
from services.bazi_engine.analysis.dayun_narrative import generate_dayun_narrative
from services.bazi_engine.analysis.wealth_estimate import estimate_wealth
from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts

__all__ = [
    "compute_wealth",
    "compute_career",
    "compute_marriage",
    "compute_health",
    "compute_relationship",
    "compute_personality",
    "compute_monthly",
    "generate_dayun_narrative",
    "estimate_wealth",
    "compute_liunian_domain_forecasts",
]
