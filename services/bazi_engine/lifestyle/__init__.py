"""lifestyle — 生活应用子包

各模块（M2.5 阶段实现）：
  tables.py     五行→生活建议映射表（WUXING_TO_COLOR/DIRECTION/NUMBER/ORGAN/JEWELRY/FENGSHUI/LIFESTYLE）
  jewelry.py    饰品推荐 → JewelryModel
  fengshui.py   风水建议 → FengshuiModel
  lucky.py      开运建议 → LuckyModel
  lifestyle.py  生活方式 → LifestyleModel

依赖规则：只依赖 tables.py 和第3层 yongshen，禁止调用 analysis/ 模块。
"""
