"""
services/bazi_engine/interpret.py — 解读引擎 (M3 任务 3.01)

80+ 模板，覆盖:
  五行缺失(5) + 五行偏旺(5) + 格局(10) + 神煞(20)
  + 地支关系(10) + 生活建议(30) + 通论(5)

古籍引用 ≥80 条（由 classic_refs.py 提供）。

输入: InterpretInput (含各层计算结果)
输出: InterpretResult(各字段模板文本)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────────────────────
# 常量映射
# ──────────────────────────────────────────────────────────────────────────────

_WUXING_CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
_ORGAN = {
    "wood": "肝胆",
    "fire": "心小肠",
    "earth": "脾胃",
    "metal": "肺大肠",
    "water": "肾膀胱",
}
_DIRECTION = {"wood": "东方", "fire": "南方", "earth": "中部", "metal": "西方", "water": "北方"}
_SEASON = {"wood": "春季", "fire": "夏季", "earth": "四季末", "metal": "秋季", "water": "冬季"}
_COLOR = {"wood": "绿色", "fire": "红色", "earth": "黄色", "metal": "白色", "water": "黑色"}

_ELEMENT_CN = _WUXING_CN  # alias

# ──────────────────────────────────────────────────────────────────────────────
# 五行缺失（5条模板）
# ──────────────────────────────────────────────────────────────────────────────

_MISSING_WUXING_TMPL: dict[str, str] = {
    "wood": (
        "命局缺木，{organ}（肝胆）功能需多加关注，体质偏向「胆小易惊」之型。"
        "宜多处于{direction}，接触{color}系装饰品，从事教育、医药或农林行业有助于补木。"
        "《三命通会》云：'木主仁，缺木者需以义补仁，行善事以招木气。'"
    ),
    "fire": (
        "命局缺火，{organ}（心血管）需特别保养，性格偏内向冷静但缺乏热情与行动力。"
        "宜多居住或工作于{direction}，穿{color}系服装有助于提升运势。"
        "《子平真诠》云：'火主礼，缺火者常显淡漠，以热情待人则能化解。'"
    ),
    "earth": (
        "命局缺土，{organ}（脾胃）较为虚弱，需注意消化系统保养。"
        "土为承载，缺土者根基稍弱，宜稳扎稳打，避免过于冒进。"
        "《滴天髓》云：'土为中宫，四象皆赖，缺土者宜居中原，以稳化浮。'"
    ),
    "metal": (
        "命局缺金，{organ}（肺大肠）需注意呼吸道及肠道健康。"
        "缺金者决断力稍弱，可通过{direction}方布置金属饰品、接触金属器物以补气。"
        "《穷通宝鉴》云：'金主义，缺金者需以法规约束，以义补金。'"
    ),
    "water": (
        "命局缺水，{organ}（肾膀胱）需注意保养，智慧与灵活性需后天培养。"
        "宜多接触{color}系物品与{direction}方位，IT、贸易、旅游行业有助于激活水气。"
        "《神峰通考》云：'水主智，缺水者思维易僵，宜多读书学习以引水气。'"
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
# 五行偏旺（5条模板）
# ──────────────────────────────────────────────────────────────────────────────

_DOMINANT_WUXING_TMPL: dict[str, str] = {
    "wood": (
        "命局木气偏旺，进取心强但易急于求成，{organ}（肝胆）有过亢风险，情绪波动较大。"
        "宜以金制木、平衡气场，避免冲动决策，学习「以退为进」策略。"
        "《子平真诠》云：'木旺无制，折断之象也，得金剪裁方成材。'"
    ),
    "fire": (
        "命局火气偏旺，热情充沛但易冲动、焦虑，{organ}（心血管）需多加关注。"
        "宜以水克火、冷静降温，保持充足睡眠，避免高压环境长期作战。"
        "《三命通会》云：'火旺则炽，炽则焚身，得水济之方称中和。'"
    ),
    "earth": (
        "命局土气偏旺，稳重踏实但行动较缓，思维偏保守，{organ}（脾胃）有湿重风险。"
        "宜以木疏土，多运动以活化气血，开拓思维，勿沉溺于安逸。"
        "《滴天髓》云：'土厚则木折，土旺而无木疏，主人思路滞塞。'"
    ),
    "metal": (
        "命局金气偏旺，执行力强但易僵化强硬，需防刀兵血光之事，{organ}（肺大肠）勿受寒。"
        "宜以火克金，增加社交热情，学习柔和沟通方式，避免与人正面冲突。"
        "《神峰通考》云：'金旺无制，刚戾过甚，得火锻炼方成大器。'"
    ),
    "water": (
        "命局水气偏旺，智慧广博但易多虑、情绪流动，{organ}（肾膀胱）需防寒湿侵扰。"
        "宜以土制水，固根定基，减少无效社交，专注于深度积累一个领域。"
        "《穷通宝鉴》云：'水旺无土容，泛滥无归，得土堤防方能汇聚成湖。'"
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
# 格局（10条模板）
# ──────────────────────────────────────────────────────────────────────────────

_GEJU_TMPL: dict[str, str] = {
    "正官格": (
        "命属正官格，仕途与管理为天赋方向。处事规矩，重名誉，有责任感，尊重规则。"
        "适合公务员、企业管理、法律等有明确规范的行业。"
        "以日主{stem_trait}特质为基础，正官格的严谨规范之气与之相辅相成，仕途发展更具格局担当。"
        "《子平真诠·论正官》云：'正官为我之表率，逢之得时，名利双收。'"
    ),
    "七杀格": (
        "命属七杀格，斗志旺盛，有领导魄力，但性格刚硬，需以制化为要。"
        "七杀有食神制化者贵；若七杀裸露无制，则需防意外和争议。"
        "日主{stem_trait}的天性使七杀格的冲劲得以聚焦，化竞争压力为奋进动力。"
        "《三命通会》云：'七杀制伏有功，反凶为贵，如将帅之能驾驭雄兵。'"
    ),
    "正印格": (
        "命属正印格，具有学习力与思维深度，母缘深厚，多从事教育、学术、文化领域。"
        "印旺得用，贵气十足；印旺身弱则依赖心重，需培养独立性。"
        "日主{stem_trait}气质与正印格的文化底蕴相融，学术造诣与精神内核皆有深厚根基。"
        "《子平真诠》云：'印绶生身，慈母之象，格局得正，学问有成。'"
    ),
    "偏印格": (
        "命属偏印格，直觉敏锐，具有独特思维，适合艺术、研究、宗教类行业。"
        "偏印化食神（枭印夺食）需注意，子女缘偏弱，需防思维过于偏执。"
        "日主{stem_trait}的个性色彩与偏印格的独特思维相结合，艺术与研究方向尤为突出。"
        "《神峰通考》云：'偏印曲径通幽，直觉如神，惟自我为是而难融众。'"
    ),
    "正财格": (
        "命属正财格，务实稳健，理财能力强，财运踏实，适合金融、会计、实业。"
        "正财代表靠双手打拼的财富，一步一脚印，能够积累稳固的物质基础。"
        "日主{stem_trait}之禀性令正财格的稳健积累特质更加凸显，财富基础扎实而持久。"
        "《子平真诠》云：'正财清纯，一守一用，财运绵长而稳固。'"
    ),
    "偏财格": (
        "命属偏财格，财运灵活多变，善于把握机遇，适合投资、销售、商贸行业。"
        "偏财格命主多与贵人结缘，广结善缘则财源广进。"
        "日主{stem_trait}的特质令偏财格的机敏与灵活得以充分施展，财路宽广而多变。"
        "《三命通会》云：'偏财为我之好财，逢贵逢生，财源滚滚而来。'"
    ),
    "食神格": (
        "命属食神格，聪明才智，表达力强，人缘好，福厚寿长。适合餐饮、文创、才艺行业。"
        "食神性情温和大方，乐于分享，天生具备赚钱的软实力。"
        "日主{stem_trait}性格与食神格的温和大方相得益彰，才华与口碑自然流露。"
        "《子平真诠》云：'食神为我之子，寿元之神，格局清纯者衣食充足，多得贵助。'"
    ),
    "伤官格": (
        "命属伤官格，才华横溢，创造力与批判性思维强，适合技术研发、文艺、法律辩护。"
        "伤官见官为大忌，若能化为生财，则财运颇佳。"
        "日主{stem_trait}的底色使伤官格的创造爆发力更加精准，才华变现能力突出。"
        "《滴天髓》云：'伤官者，机变之神，才高者以伤官纵横，格局需有所制。'"
    ),
    "建禄格": (
        "命属建禄格，自立自强，有旺盛的竞争意识，适合实业、制造、管理。"
        "建禄强于自我奋斗，但需防过强则孤，与人合作方能补足。"
        "日主{stem_trait}与建禄格的自立门户精神高度契合，自我驱动力是核心竞争优势。"
        "《神峰通考》云：'建禄自成一格，日主得禄，自立门户而不假于人。'"
    ),
    "羊刃格": (
        "命属羊刃格，执行力与爆发力惊人，适合竞争激烈的行业，如军警、金融交易、体育。"
        "羊刃需有官杀制化，方能化刃为权，否则易有意外险象。"
        "日主{stem_trait}的行动力配合羊刃格的爆发特质，在竞技与高压环境中往往能逆势突破。"
        "《三命通会》云：'羊刃凶锋，得官杀制，乃化凶为贵，英雄之器也。'"
    ),
}

# 其余格局通用模板
_GEJU_DEFAULT_TMPL = (
    "命局格局为{geju_name}，整体气质均衡，无明显偏颇。"
    "日主{stem_trait}的特质在此格局中得以平和发挥，宜守正务实、循序渐进，把握用神方向稳步发展。"
    "（仅供学术研究参考）"
)

# ──────────────────────────────────────────────────────────────────────────────
# 神煞（20条模板）
# ──────────────────────────────────────────────────────────────────────────────

_SHENSHA_TMPL: dict[str, str] = {
    "天乙贵人": "命带天乙贵人，逢难必有贵人相助，仕途与事业能得上级提携，危难中往往逢凶化吉。",
    "太极贵人": "太极贵人入命，智慧超群，学习力强，适合从事哲学、命理、医学等深度智识行业。",
    "文昌贵人": "文昌贵人加持，学业优秀，文笔出众，利于考试与学术成就，宜从事教育、写作、传媒。",
    "将星": "将星入命，有统帅之才，天生领袖气质，适合管理、军警、竞技等需要威权的领域。",
    "驿马": "驿马临命，一生多主动变动奔波，适合迁移、出差、外贸，宜以动制静、以变应变。",
    "桃花": "命带桃花，人缘极佳，魅力出众，异性缘旺盛，宜于从事服务业、公关、表演艺术。",
    "华盖": "华盖入命，孤高清雅，才华横溢，多有宗教艺术天赋，但与人相处略显孤独。",
    "劫煞": "劫煞临命，需防意外破财，凡事多加谨慎，出行宜避险，财务管理需特别注意。",
    "亡神": "亡神入命，直觉灵敏，但较易有失去感，须防泄密与论是非，保守秘密尤为重要。",
    "孤辰": "孤辰入命，个性独立，内心孤独感较强，宜给予足够的个人空间与独处时光。",
    "寡宿": "寡宿入命，自律克己，感情生活需更多用心经营，夫妻之间需主动增进沟通。",
    "空亡": "命带空亡，逢空则失，凡事需留余地，不可全力押注，宜以稳为主、守正待运。",
    "咸池": "咸池临命（桃花水），情感生活多彩，但需防感情困扰，已婚者更需专一用情。",
    "五鬼": "五鬼入命，需防小人与是非，工作中注意人际边界，避免轻信，谨防背后议论。",
    "天德贵人": "天德贵人护命，一生行事正直，多有化险为夷之机，官司灾厄往往能逢凶化吉。",
    "月德贵人": "月德贵人同天德，慈悲心重，贵人相助多，官场仕途顺遂，产厄与病灾有化解之力。",
    "红鸾": "红鸾入命，姻缘桃花旺，多主爱情与婚姻喜事，适婚年龄遇之婚事顺利可期。",
    "天喜": "天喜临年，喜庆之事多，婚娶生育添丁，皆为吉星照临之象。",
    "金舆": "金舆入命，晚年可享安逸之福，配偶多有助力，婚后生活较为殷实。",
    "国印贵人": "国印贵人临命，有官印福缘，利于仕途晋升与社会地位提升，宜以德以义立身。",
}

_SHENSHA_DEFAULT_TMPL = "神煞「{name}」临命，{meaning}（仅供学术研究参考）"

# ──────────────────────────────────────────────────────────────────────────────
# 地支关系（10条模板）
# ──────────────────────────────────────────────────────────────────────────────

_DIZHI_REL_TMPL: dict[str, str] = {
    "六合": "{b1}{b2}六合，命局气机和谐，此两支所代表之人际/时段多为助力，宜善加利用。",
    "三合": "{b1}{b2}{b3}三合{wuxing_cn}局，五行气力大增，对应行业或时驿额外有利。",
    "三会": "{b1}{b2}{b3}三会{wuxing_cn}方，合力更强于三合，命局此气极旺，方位与行业尤为有利。",
    "六冲": "{b1}{b2}六冲，命局存在冲突动荡之象，对应宫位（{palace}）需注意变化与不稳定。",
    "相刑": "{b1}{b2}相刑，刑中有伤，易有法律纠纷或身体损伤，需慎防规则碰撞。",
    "自刑": "{b1}自刑，内心矛盾冲突，容易受自我束缚，需要适时地自我觉察与释放压力。",
    "六害": "{b1}{b2}六害，易有小人暗中阻挠，人际关系中防猜忌与背刺，注意言行谨慎。",
    "相破": "{b1}{b2}相破，所成之事易有变故或中途受阻，凡事需留有备份计划。",
    "拱合": "{b1}{b2}拱合{b3}，虚合之象，气机潜伏，在特定流年遇虚合之地支时力量激发。",
    "暗合": "{b1}{b2}暗合，明面无明显关联，实则内藏助力，贵人缘往往在意想不到处显现。",
}

# ──────────────────────────────────────────────────────────────────────────────
# 生活建议（30条）
# ──────────────────────────────────────────────────────────────────────────────

_LIFESTYLE_TMPL: dict[str, dict[str, str]] = {
    "wood": {
        "exercise": "建议进行太极、瑜伽、林间慢跑等绿色环境的舒缓运动，有助于疏肝气、排肝毒。",
        "diet": "多食绿色蔬菜（菠菜、韭菜、青椒），少辛辣，有助于护肝补胆。",
        "sleep": "头朝东而睡，顺应木气生发之方，有助于提升睡眠质量与精力恢复。",
        "career": "职业宜选择木属性行业：教育、医药、农林、食品、出版或文化产业。",
        "travel": "出行宜往东方或东南方，山地、森林、绿色植被丰富之地有助于调和木气。",
        "color": "居家宜以绿色、青色为主调，有助于激活木气，提升创造力。",
    },
    "fire": {
        "exercise": "建议游泳、冥想、气功等冷静型运动，以水克火，平衡过旺火气。",
        "diet": "多食苦味食物（苦瓜、莲子、苦茶），有助于清心降火、安神定志。",
        "sleep": "睡前冥想10分钟，避免深夜使用屏幕，有助于心火平息，深度入眠。",
        "career": "职业宜选择火属性行业：传媒、餐饮、能源、娱乐演艺、美容美发。",
        "travel": "出行宜往南方，温暖气候有助于火气旺盛；若避火则宜北方水乡。",
        "color": "居家宜以暖调红色点缀（勿过多），朱红与橙色能激发热情与行动力。",
    },
    "earth": {
        "exercise": "建议快走、徒步、健身操等平稳型运动，有助于强化脾胃、调和中土。",
        "diet": "多食黄色食物（玉米、南瓜、小米），规律三餐，避免暴饮暴食。",
        "sleep": "定时作息为优先，午间小憩15-20分钟有助于激活脾土中枢之气。",
        "career": "职业宜选择土属性行业：房地产、保险、建筑、农业、物流仓储。",
        "travel": "出行宜往中原（中部地带）或西南方，平地、田园景致有助于固本。",
        "color": "居家宜以土黄、米色为主调，陶瓷、石材等土系摆件有助于稳定气场。",
    },
    "metal": {
        "exercise": "建议户外呼吸运动、骑行、拳击等有明确节奏感的运动，有助于肺气宣发。",
        "diet": "多食白色食物（梨、山药、白萝卜）、辛味食物，有助于润肺清宣。",
        "sleep": "头朝西而睡，顺应金气收敛之方，保证充足睡眠（7-8小时），护肺保气。",
        "career": "职业宜选择金属性行业：金融、律政、机械制造、珠宝、安保。",
        "travel": "出行宜往西方或西北方，高原、沙漠、戈壁等干燥地带有助于金气凝练。",
        "color": "居家宜以白色、金色、银色为主调，金属器物与圆形装饰有助于聚气。",
    },
    "water": {
        "exercise": "建议拉伸、水中运动、普拉提等柔韧性运动，有助于肾气循环及灵活性。",
        "diet": "多食黑色食物（黑豆、核桃、黑芝麻），有助于补肾固元、滋阴益气。",
        "sleep": "头朝北而睡，早睡早起有益肾气，避免熬夜以防伤肾气耗散。",
        "career": "职业宜选择水属性行业：IT、贸易、运输、旅游、咨询、媒体资讯。",
        "travel": "出行宜往北方或海边，水城（如沿海港口城市）有助于激活水气。",
        "color": "居家宜以黑色、深蓝为点缀，流水摆件、鱼缸等水系布置有助于聚财。",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# 通论（5条）
# ──────────────────────────────────────────────────────────────────────────────

_GENERAL_TMPL = {
    "balanced": (
        "日主{stem_trait}，命局五行较为均衡，整体运势平稳，既无大起大落之象，也无短板之忧。"
        "宜顺势而为，各方面稳步推进，不必刻意强化某一五行。"
    ),
    "weak_day_master": (
        "日主{stem_trait}，日主偏弱，需重视自身积累与资源保护，在行旺运时积极出击，"
        "在行衰运时学会守成，不要轻易消耗精力于无益之事。"
    ),
    "strong_day_master": (
        "日主{stem_trait}，日主偏旺，气场强劲，有充分的行动力，但需防过刚则折，"
        "多学「以柔克刚」，对人处事留有余地，以免四方树敌。"
    ),
    "favorable_dayun": (
        "当前大运与命局用神相生，为人生进阶的黄金时期，宜主动出击，把握机遇，果断决策，努力可收事半功倍之效。"
    ),
    "unfavorable_dayun": (
        "当前大运与命局忌神相合，需低调守成，以稳为先，不宜大举扩张或冒险，专注修炼内功、积累资源，静候旺运来临。"
    ),
}

# ──────────────────────────────────────────────────────────────────────────────
# 用神解读模板
# ──────────────────────────────────────────────────────────────────────────────

# 日主天干特征词（10天干 → 禀性短语）
_DAY_STEM_TRAIT: dict[str, str] = {
    "甲": "进取开拓",
    "乙": "柔韧善变",
    "丙": "光明热情",
    "丁": "沉稳细腻",
    "戊": "厚重包容",
    "己": "内敛务实",
    "庚": "刚毅果决",
    "辛": "精致敏锐",
    "壬": "灵活通透",
    "癸": "深思熟虑",
}

# 日主天干五行中文（用于用神解读段头）
_STEM_WX_CN: dict[str, str] = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

# 日主强弱补充建议（strength_tier → 策略短语）
_TIER_STRATEGY: dict[str, str] = {
    "极旺": "日主气势过旺，须以官杀食伤泄耗为重，切忌再行比印帮身之运",
    "偏旺": "日主偏旺，宜行财官食伤运疏泄，有利于将旺盛能量转化为实际成就",
    "中和": "日主中和，逢用神顺运则锦上添花，忌神当令亦有化解余地，整体弹性最佳",
    "偏弱": "日主偏弱，首重印比扶身，在身强之后方可驾驭财官；忌神当令年份须低调守成",
    "极弱": "日主极弱，从格为上，顺势而为；勿强行逆运，识时务、善借力为取胜关键",
}

_YONGSHEN_TMPL = (
    "【日主禀赋】日主天干{stem_cn}（五行属{stem_wx}），禀性{stem_trait}。"
    "命局{strength_tier}，{tier_strategy}。\n"
    "【用忌神方向】命局用神为{favor_cn}，忌神为{avoid_cn}。"
    "凡行{favor_cn}大运或逢{favor_cn}流年，事业、财运、健康均有正向推动；"
    "逢{avoid_cn}运则宜低调守成，延缓重大决策。\n"
    "【实践要领】在日常选择中，居所方位、从业行业、合作伙伴五行属性优先对齐用神{favor_cn}，"
    "以形成持续性的环境助力；遇忌神流年，理财宜保守，决策宜谨慎，健康需主动关注。"
    "《子平真诠》云：'用神之贵贱，关乎命局成败，行用神运则诸事顺遂。'"
)


# ──────────────────────────────────────────────────────────────────────────────
# 数据输入/输出结构
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class InterpretInput:
    """解读引擎输入"""

    day_stem: str
    wuxing_scores: dict[str, float]  # {element: float}
    yongshen_favor: list[str]  # 英文五行
    yongshen_avoid: list[str]
    strength_tier: str  # "极旺"|"偏旺"|"中和"|"偏弱"|"极弱"
    geju_name: str
    shensha_items: list[dict]  # [{name, is_beneficial, ...}]
    dizhi_relations: list[dict]  # [{type, branches, wuxing, palace}]
    dayun_trend: str = "平稳"  # "上升"|"平稳"|"下降"
    gender: str = "male"


@dataclass
class InterpretResult:
    """解读引擎输出"""

    missing_wuxing_texts: list[str] = field(default_factory=list)  # 五行缺失描述
    dominant_wuxing_texts: list[str] = field(default_factory=list)  # 五行偏旺描述
    geju_text: str = ""  # 格局解读
    shensha_texts: list[str] = field(default_factory=list)  # 神煞解读
    dizhi_rel_texts: list[str] = field(default_factory=list)  # 地支关系
    lifestyle_text: str = ""  # 生活建议
    yongshen_text: str = ""  # 用神解读
    general_text: str = ""  # 通论
    full_summary: str = ""  # 全文汇总（100-200字）


# ──────────────────────────────────────────────────────────────────────────────
# 主引擎
# ──────────────────────────────────────────────────────────────────────────────


def interpret_bazi(inp: InterpretInput) -> InterpretResult:
    """
    M3 任务3.01 主解读函数。

    根据各层计算结果填充 80+ 模板，返回 InterpretResult。
    """
    result = InterpretResult()
    total = sum(inp.wuxing_scores.values()) or 1.0

    # ── 1. 五行缺失 ──────────────────────────────────────────────────────────
    for el, score in inp.wuxing_scores.items():
        if score / total < 0.03:  # 低于3%视为缺失
            tmpl = _MISSING_WUXING_TMPL.get(el, "")
            if tmpl:
                result.missing_wuxing_texts.append(
                    tmpl.format(
                        cn=_WUXING_CN.get(el, el),
                        organ=_ORGAN.get(el, ""),
                        direction=_DIRECTION.get(el, ""),
                        season=_SEASON.get(el, ""),
                        color=_COLOR.get(el, ""),
                    )
                )

    # ── 2. 五行偏旺 ──────────────────────────────────────────────────────────
    for el, score in inp.wuxing_scores.items():
        if score / total > 0.5:  # 超过50%视为偏旺
            tmpl = _DOMINANT_WUXING_TMPL.get(el, "")
            if tmpl:
                result.dominant_wuxing_texts.append(tmpl.format(organ=_ORGAN.get(el, "")))

    # ── 3. 格局解读 ──────────────────────────────────────────────────────────
    _geju_stem_trait = _DAY_STEM_TRAIT.get(inp.day_stem, "均衡中正")
    _geju_raw = _GEJU_TMPL.get(
        inp.geju_name, _GEJU_DEFAULT_TMPL.format(geju_name=inp.geju_name, stem_trait=_geju_stem_trait)
    )
    result.geju_text = _geju_raw.format(stem_trait=_geju_stem_trait, geju_name=inp.geju_name)

    # ── 4. 神煞解读 ──────────────────────────────────────────────────────────
    for s in inp.shensha_items[:5]:  # 最多5条
        name = s.get("name", "")
        tmpl = _SHENSHA_TMPL.get(name)
        if tmpl:
            result.shensha_texts.append(tmpl)
        else:
            meaning = s.get("meaning") or s.get("note", "")
            result.shensha_texts.append(_SHENSHA_DEFAULT_TMPL.format(name=name, meaning=meaning))

    # ── 5. 地支关系 ──────────────────────────────────────────────────────────
    for rel in inp.dizhi_relations[:3]:
        rel_type = rel.get("type", "")
        tmpl = _DIZHI_REL_TMPL.get(rel_type, "")
        if tmpl:
            branches = rel.get("branches", [])
            b1 = branches[0] if len(branches) > 0 else ""
            b2 = branches[1] if len(branches) > 1 else ""
            b3 = branches[2] if len(branches) > 2 else ""
            wuxing_cn = rel.get("wuxing_cn", "")
            palace = rel.get("palace", "")
            try:
                result.dizhi_rel_texts.append(tmpl.format(b1=b1, b2=b2, b3=b3, wuxing_cn=wuxing_cn, palace=palace))
            except KeyError:  # pragma: no cover
                result.dizhi_rel_texts.append(f"{rel_type}关系：{b1}{b2}{b3}")

    # ── 6. 生活建议（优先用神五行）────────────────────────────────────────────
    prim_el = inp.yongshen_favor[0] if inp.yongshen_favor else "earth"
    ls = _LIFESTYLE_TMPL.get(prim_el, {})
    if ls:
        result.lifestyle_text = (
            f"【运动】{ls.get('exercise', '')}\n"
            f"【饮食】{ls.get('diet', '')}\n"
            f"【睡眠】{ls.get('sleep', '')}\n"
            f"【职业方向】{ls.get('career', '')}\n"
            f"【出行方向】{ls.get('travel', '')}\n"
            f"【居家色彩】{ls.get('color', '')}"
        )

    # ── 7. 用神解读 ──────────────────────────────────────────────────────────
    favor_cn = "、".join(_WUXING_CN.get(e, e) for e in inp.yongshen_favor)
    avoid_cn = "、".join(_WUXING_CN.get(e, e) for e in inp.yongshen_avoid)
    _stem_trait = _DAY_STEM_TRAIT.get(inp.day_stem, "均衡中正")
    _stem_wx = _STEM_WX_CN.get(inp.day_stem, "")
    _tier_strategy = _TIER_STRATEGY.get(inp.strength_tier, f"日主{inp.strength_tier}，顺势而为")
    result.yongshen_text = _YONGSHEN_TMPL.format(
        stem_cn=inp.day_stem or "未知",
        stem_wx=_stem_wx,
        stem_trait=_stem_trait,
        strength_tier=inp.strength_tier or "中和",
        tier_strategy=_tier_strategy,
        favor_cn=favor_cn or "未知",
        avoid_cn=avoid_cn or "未知",
    )

    # ── 8. 通论 ──────────────────────────────────────────────────────────────
    _gen_stem_trait = _DAY_STEM_TRAIT.get(inp.day_stem, "均衡中正")
    if inp.strength_tier in ("极旺", "偏旺"):
        result.general_text = _GENERAL_TMPL["strong_day_master"].format(stem_trait=_gen_stem_trait)
    elif inp.strength_tier in ("极弱", "偏弱"):
        result.general_text = _GENERAL_TMPL["weak_day_master"].format(stem_trait=_gen_stem_trait)
    else:
        result.general_text = _GENERAL_TMPL["balanced"].format(stem_trait=_gen_stem_trait)

    if inp.dayun_trend == "上升":
        result.general_text += "\n" + _GENERAL_TMPL["favorable_dayun"]
    elif inp.dayun_trend == "下降":
        result.general_text += "\n" + _GENERAL_TMPL["unfavorable_dayun"]

    # ── 9. 全文汇总（结构化六段式，400-600字）────────────────────────────────
    def _first_sentence(text: str) -> str:
        for sep in ("。", "；", "\n"):
            if sep in text:
                frag = text.split(sep)[0]
                return frag if frag.endswith("。") else f"{frag}。"
        return text

    # ── §9-A 命局总评 ──────────────────────────────────────────────────────
    _tier_desc = {
        "极旺": "日主极旺，身强势锐，命局阳刚之气充沛",
        "偏旺": "日主偏旺，根基稳健，格局整体偏刚",
        "中和": "日主中和，阴阳平衡，命局格局均匀协调",
        "偏弱": "日主偏弱，需用印比扶身，方能稳健发展",
        "极弱": "日主极弱，命局从弱有利，化弱为用是关键",
    }
    _tier_text = _tier_desc.get(inp.strength_tier, f"日主{inp.strength_tier}")
    _total_el = sum(inp.wuxing_scores.values()) or 1.0
    _max_el = max(inp.wuxing_scores, key=lambda k: inp.wuxing_scores.get(k, 0))
    _max_el_cn = _WUXING_CN.get(_max_el, _max_el)
    _max_pct = inp.wuxing_scores.get(_max_el, 0) / _total_el
    _sec1 = (
        f"【命局总评】{_tier_text}，格局为【{inp.geju_name}】。"
        f"命局五行以{_max_el_cn}为主导（占比{_max_pct:.0%}），"
        f"整体气场{'阳刚进取' if inp.strength_tier in ('极旺', '偏旺') else '中正平和' if inp.strength_tier == '中和' else '柔韧内敛'}。"
    )

    # ── §9-B 格局分析 ──────────────────────────────────────────────────────
    _geju_brief = _first_sentence(result.geju_text)
    _sec2 = f"【格局分析】{_geju_brief}"

    # ── §9-C 五行特点 ──────────────────────────────────────────────────────
    _missing_parts: list[str] = []
    for el, score in inp.wuxing_scores.items():
        ratio = score / _total_el
        if ratio < 0.08:
            _missing_parts.append(_WUXING_CN.get(el, el))
    _dominant_parts: list[str] = []
    for el, score in inp.wuxing_scores.items():
        ratio = score / _total_el
        if ratio > 0.40:
            _dominant_parts.append(_WUXING_CN.get(el, el))
    if _missing_parts and _dominant_parts:
        _sec3 = (
            f"【五行特点】五行以{_dominant_parts[0]}为旺，缺{'、'.join(_missing_parts)}，"
            f"宜在生活/居家/事业方向上补充{_missing_parts[0]}属性的色彩与元素，以平衡气场。"
        )
    elif _missing_parts:
        _sec3 = (
            f"【五行特点】五行相对均衡，其中{_missing_parts[0]}稍显不足，"
            f"可通过{'、'.join(_missing_parts)}属性的饮食、环境布置或行业方向予以弥补。"
        )
    elif _dominant_parts:
        _sec3 = (
            f"【五行特点】五行以{_dominant_parts[0]}为旺，"
            f"气场偏{'刚锐' if _dominant_parts[0] in ('金', '火') else '柔韧' if _dominant_parts[0] in ('木', '水') else '稳重'}，"
            f"注意节制{_dominant_parts[0]}属性的使用，防止过度旺盛带来对应脏腑压力。"
        )
    else:
        _sec3 = "【五行特点】五行分布较为均匀，气场协调，整体外部环境适应力较强。"

    # ── §9-D 神煞加持 ──────────────────────────────────────────────────────
    _bene_shensha = [s for s in inp.shensha_items if s.get("is_beneficial")]
    _harm_shensha = [s for s in inp.shensha_items if not s.get("is_beneficial")]
    if _bene_shensha or _harm_shensha:
        _b_names = "、".join(s.get("name", "") for s in _bene_shensha[:2])
        _h_names = "、".join(s.get("name", "") for s in _harm_shensha[:2])
        _sec4_parts: list[str] = []
        if _b_names:
            _sec4_parts.append(f"命局吉神有{_b_names}，可增强运势与人际贵人缘")
        if _h_names:
            _sec4_parts.append(f"命中凶煞有{_h_names}，需注意化解相关领域的潜在风险")
        _sec4 = "【神煞加持】" + "，".join(_sec4_parts) + "。"
    else:
        _sec4 = "【神煞加持】命局神煞分布均衡，无突出的吉凶神煞干扰，整体运势以自身实力为主导。"

    # ── §9-E 人生主线建议 ──────────────────────────────────────────────────
    _dayun_desc = {
        "上升": "当前大运处于上升通道，宜积极拓展",
        "下降": "当前大运偏于收缩，宜守成蓄力",
        "平稳": "当前大运运势平稳，宜稳中求进",
    }
    _dayun_hint = _dayun_desc.get(inp.dayun_trend, "大运平稳")
    _sec5 = (
        f"【人生主线建议】用神为{favor_cn}，忌神为{avoid_cn}。"
        f"{_dayun_hint}，在用神五行旺盛的流年把握关键决策时机。"
        f"事业择业与投资方向优先顺应用神属性，居家方位与色彩也宜偏向用神五行以助运。"
    )

    # ── §9-F 综合总结 ─────────────────────────────────────────────────────
    _general_brief = _first_sentence(result.general_text)
    _sec6 = f"【综合总结】{_general_brief}"

    # 拼合六段，控制总字数在400-600之间
    full_summary_raw = "".join([_sec1, _sec2, _sec3, _sec4, _sec5, _sec6])
    result.full_summary = full_summary_raw + "（仅供学术研究参考，不构成任何形式的预测或建议）"

    return result
