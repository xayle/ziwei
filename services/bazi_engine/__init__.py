"""
services/bazi_engine — 八字命理计算引擎包（v7.0）

包结构（按依赖层级）：
  第0层 — 基础数据（无任何依赖）
    tables.py           11张查找表 + self_check()
    solar_time_v2.py    Spencer EoT 公式（M1 任务 1.02）
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

切换开关：
  ENGINE_V2=true  → 走本包新路径
  ENGINE_V2=false → fallback 到旧 bazi_full_service.py（默认，M1 完成前保持）

当前状态：空包占位，M1 开始时逐步填充各模块。
"""
