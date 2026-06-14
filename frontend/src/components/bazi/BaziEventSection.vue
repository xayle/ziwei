<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventPrediction } from '@/composables/useEventPrediction'
import {
  RISK_LABEL,
  EVENT_DISPLAY,
  SIGNAL_LAYER_LABEL,
  type EventType,
} from '@/api/eventPrediction'

const props = defineProps<{
  caseId: string | null
}>()

const emit = defineEmits<{
  (e: 'open-save-dialog'): void
}>()

const ALL_EVENT_TYPES: EventType[] = ['marriage', 'wealth', 'property', 'career', 'health']

// 将 caseId prop 转为 Ref<string|null> 供 useEventPrediction 使用
const caseIdRef = computed(() => props.caseId)

const {
  selectedYear:       evtYear,
  selectedEventType:  evtType,
  eventData:          evtData,
  trendData:          evtTrend,
  consultText:        evtConsultText,
  consultLoading:     evtConsultLoading,
  eventLoading:       evtLoading,
  trendLoading:       evtTrendLoading,
  currentEventResult: evtResult,
  followupQuestions:  evtFollowups,
  trendSummaries:     evtSummaries,
  timelineSummary:    evtTimelineSummary,
  consultError:       evtConsultError,
  fetchYearEvents,
  fetchTrend,
  consult:            evtConsult,
  selectYear,
  selectEventType,
} = useEventPrediction(caseIdRef)

const evtUserQuestion = ref('')

// 当 caseId 设置后自动加载趋势与年份事件
watch(caseIdRef, (id) => {
  if (id) {
    fetchTrend()
    fetchYearEvents()
  }
})

async function handleEvtConsult(question: string) {
  evtUserQuestion.value = question
  await evtConsult(question)
}

// ======== 三法深度 AI 咨询 ========
type MethodKey = 'bazi' | 'heluo' | 'qimen'

interface ConsultMode {
  key: string
  label: string
  icon: string
  getPrompt: (extra?: Record<string, string>) => string
}

const DEPTH_PREFIX = `⚠️ 深度分析要求：本次分析必须详尽具体，严格遵守以下规范：
・每个分析板块不少于200字，不得以一句话或列点简略带过
・财富/收入数据必须给具体数字区间（如"年入20-40万"），不得使用"有所提升""较好"等模糊表述
・年份、大运、流年一律给出具体年份数字和干支，不得使用"某个阶段""近年来"
・涉及感情/婚姻，配偶特征必须具体描述（性格/职业/优缺点），不得回避或以空洞形容词替代
・总字数不少于1500字（完整命盘/三问类不少于2000字）
・语言风格：直接诚实，不客套，禁用"仅供参考""因人而异""命理仅供参考"等套话

`

const activeMethod = ref<MethodKey>('bazi')

const METHODS: { key: MethodKey; label: string; desc: string }[] = [
  { key: 'bazi',  label: '八字法',   desc: '命局·大运·流年深析' },
  { key: 'heluo', label: '河洛易数', desc: '起卦·卦象·体用推演' },
  { key: 'qimen', label: '奇门遁甲', desc: '值符·三问·事项判断' },
]

const activeSubMode = ref<string>('bazi_full')
const qimenExtra = ref({ year: '', event: '', direction: '' })

const BAZI_MODES: ConsultMode[] = [
  {
    key: 'bazi_full', label: '完整命盘', icon: '命',
    getPrompt: () => DEPTH_PREFIX + `请以命理师口吻分析本人完整命盘，语言直接不客套，财富给具体数字区间：

一、命局核心结论
・日主五行与强弱（给出判断依据与核心依据星，说明为何强/弱）
・用神、忌神（明确原因，各举1-2个具体例证说明其作用）
・格局定性（普通命/中产命/富贵命，直接给等级，说明理由，不得模糊）
・一生财富天花板：最高年收入XX-XX万（说明依据是哪颗星、哪个大运）

二、大运详解（每运四项全写，不得省略任何一项）
每运格式：【大运天干地支】（XX-XX岁，XXXX-XXXX年）
财富：年收入走势（给区间数字分前五年/后五年，如"前五年年入10-20万，后五年年入20-35万"）
事业：最适合的行业/方向与关键变动年份（至少给1个关键年份+该年会发生什么）
健康：主要风险脏腑或症状倾向与高风险年（至少给1个具体年份）
感情：感情走向与重要节点年份（至少给1个具体节点+该节点发生什么）

三、财富总量估算
・一生净存款区间（XX-XX万），说明理由
・最佳赚钱期：XX-XX岁（XXXX-XXXX年），说明为何是最佳期
・最大破财期：XX-XX岁，说明原因和应对方式
・最适合的3种具体财富来源类型（如"互联网/技术服务"而非"做生意"）

四、婚姻与子女
・婚次预测与各任配偶特征（性格特点3条、职业倾向、优缺点各2条，不得用"温柔体贴"等空洞词）
・初婚年龄区间（XX-XX岁）
・子女缘分薄厚与子女人数倾向

五、最终结论
・一句话核心评语（诚实，不温和，直接说命格等级与核心议题）

六、命主核心人生矛盾与战略建议
・用神与忌神在人生中的反复博弈，举2个具体时间节点举例（XXXX年发生X，因为XX干支与日主XX关系……）
・最适合命主的3条具体可操作人生战略建议（每条结合命格特点，可操作，不抽象）`,
  },
  {
    key: 'bazi_dayun', label: '当前大运', icon: '运',
    getPrompt: () => DEPTH_PREFIX + `请重点分析本人当前所走大运，严格按以下结构详细输出，每项不少于200字：

一、大运五行影响
・大运天干与日主、用神的具体生克关系（逐一分析：天干与日主五行何种关系，对用神有何影响）
・大运地支与命局地支的冲合刑会（具体说明哪两支相冲/合，产生何种效应）
・这十年整体走势：提升/平稳/下降（给明确判断 + 判断依据，说明哪几年是关键转折点）

二、财富解析（必须给数字）
・这十年前五年年收入走势区间（XX-XX万）& 后五年年收入走势区间（XX-XX万）
・最佳财运年份（给2个具体年份+干支+星象分析+操作建议）
・破财风险年份（给1个具体年份+干支+为什么+规避方式）

三、事业解析
・当前最适合的行业/职业方向（具体行业，说明为何此大运利此行业）
・关键升迁/转型年份（给1-2个具体年份+该年命格支持什么方向的变动）
・最需回避的职业/行业方向与错误操作（具体说是什么，不能笼统说"不利的事"）

四、健康解析
・这十年主要健康风险（具体脏腑或症状倾向，说明与大运何星何宫的关系）
・高风险年份（给1-2个具体年份）及养生注意事项

五、感情解析
・这十年感情整体走势（主动/被动，稳定/动荡，说明原因）
・婚变/关键感情节点年份（给具体年份+干支+会发生什么）

六、大运核心建议（一句话，直接）

七、大运结束后的过渡预判
・下一步大运干支 + 交接年份（XXXX年）的注意事项与最值得把握的机遇窗口`,
  },
  {
    key: 'bazi_year', label: '流年精析', icon: '年',
    getPrompt: () => DEPTH_PREFIX + `请重点分析本人${new Date().getFullYear()}年流年，按以下结构详细输出，每项充分分析：

一、流年干支对命局的三重影响
・流年天干与日主/用神的生克关系（分析天干五行对用神的具体影响）
・流年地支与命局地支的冲合刑会（具体说哪两支发生了何种关系，效应如何）
・流年+大运+命局三重叠加的综合判断（说明三重叠加后整体是吉是凶，给判断依据）
・今年整体定性：吉年/平年/凶年（明确给出 + 理由）

二、今年财运（必须给数字）
・今年可能实现的收入区间（XX-XX万），说明哪颗星支持此判断
・最佳进财时机（给具体月份区间，如3-5月、9-10月，说明为何是这几个月）
・今年有无横财/偏财机会：明确回答有或没有（有则说明类型和时间窗口）

三、今年事业
・关键机会点在哪个月份区间（给具体月份+说明该月命格支持何种行动）
・需要把握的具体行动方向（可操作的建议，不能是"积极进取"等空话）
・需要回避的错误操作（具体说什么不能做，为什么）

四、今年感情
・已婚者：婚姻是否有波动节点（给月份+说明该月发生什么类型的事）
・未婚者：今年有无桃花/遇到合适对象的时机（给月份区间+说明什么类型的人）

五、今年健康
・今年主要健康隐患（具体部位或症状，说明与流年何干支有关）
・高风险月份（给具体月份+风险内容）

六、今年日历：最值得把握的3个月
（每月：具体月份 + 为何有利 + 可操作建议）

七、今年日历：最需回避的2个高风险月
（每月：具体月份 + 风险类型 + 防范措施）`,
  },
  {
    key: 'bazi_wealth', label: '财富轨迹', icon: '财',
    getPrompt: () => DEPTH_PREFIX + `请专注分析本人一生财富轨迹，按以下结构详细输出，每项不少于200字：

一、财富基础格局
・财星强弱与质量（正财星/偏财星分别是哪颗，与日主和用神是何关系，强旺还是受克）
・天生财富等级定位（直接给：普通/小康/中产/富裕，并说明3条具体理由）
・财富来源类型（工资收入/自营/投资/偏财，哪种最匹配此命格，为什么）

二、各大运财富走势（每运给数字，必须逐运全写）
每运格式：【大运名】（XX-XX岁，XXXX-XXXX年）
前五年年收入区间：XX-XX万
后五年年收入区间：XX-XX万
资产积累速度：快/中/慢（原因）
是否有暴富/破财风险年：有则给具体年份+原因

三、人生三个财富关键期
・第一个财富机遇期：XX-XX岁（XXXX-XXXX年）
  为何是机遇期（说明命理依据）+ 具体操作建议（可执行）
・第二个财富爆发期：XX-XX岁（XXXX-XXXX年）
  为何是爆发期（说明命理依据）+ 最优策略（具体）
・最大破财风险期：XX-XX岁（XXXX-XXXX年）
  破财机制（说明为何此期破财）+ 防范措施（具体可执行）

四、一生财富总量估算
・退休时净资产区间（XX-XX万），说明计算逻辑
・最适合的3种具体赚钱方式（如"做制造业供应链"而非"做生意"）
・最容易破财的3种具体模式（如"股票杠杆"而非"投资失当"）

五、财富命格总结（一句话，直接说结论）

六、针对本命格的3条具体理财策略
（每条不少于100字，结合命格特点给出可操作建议，说明"此命格XX星特点，所以应该……避免……"）`,
  },
  {
    key: 'bazi_marriage', label: '婚姻感情', icon: '情',
    getPrompt: () => DEPTH_PREFIX + `请专注分析本人婚姻感情命格，按以下结构详细输出，每项不少于200字：

一、感情基础格局
・夫妻星质量及与日主的关系（正官/七杀/食神/伤官等，具体分析星名+五行+与日主的生克）
・感情模式定性（主动还是被动，依赖型还是独立型，忠诚度倾向，为什么）
・婚姻层次匹配度（配偶大致层次 vs 自身层次，是否相称，说明依据）

二、各大运感情走势（逐运全写）
每运格式：【大运名】（XX-XX岁）
感情整体状态：高涨/平稳/动荡（说明原因）
重要桃花/感情变动年份：给具体年份+该年会发生什么
婚变风险年份：有则给具体年份（无则说无）

三、婚姻关键事件预测
・初婚年龄区间（XX-XX岁），说明命格依据
・配偶特征（必须具体，格式：性格特点3条/职业倾向/外貌倾向/优点2条/缺点2条，禁用"温柔体贴""上进好学"等空洞词）
・婚次预测：直接说一婚到底还是有二婚迹象，给判断依据
・子女：几个子女倾向？男女比例？子女与命主关系是亲密还是疏离？

四、感情关键警示
・最容易出问题的年龄段（给具体范围，说明为什么这段时间）
・最需要避开的感情/婚姻类型（具体描述什么类型的人会带来问题）
・命格中感情的核心议题是什么（一句话点出最深层的感情模式）

五、婚恋总结（一句话，诚实直接，说明命主在感情上的整体格局）

六、命主在感情中最容易陷入的3个坑
（每条：具体场景描述 + 为什么会陷入（命格原因）+ 解决方案（可操作））`,
  },
]

const HELUO_MODES: ConsultMode[] = [
  {
    key: 'heluo_gua', label: '起卦推演', icon: '卦',
    getPrompt: () => DEPTH_PREFIX + `请用河洛易数为本人推演命盘卦象，按以下结构详细输出，每项不少于200字：

一、起卦过程（必须展示计算步骤）
・依生辰起天地数（展示具体数值计算过程：天数 / 地数 / 合数 / 余数）
・余数确定本卦（哪一卦：卦名 + 卦象符号 + 卦义说明，不少于100字）
・变爻位置（第几爻变，变卦名称 + 卦义，说明变化含义）
・互卦截取（三到五爻互得哪卦，卦名 + 卦义 + 与本卦的关系）

二、体用判定
・体卦与用卦的确认（依生日奇偶确定，明确说明哪宫是体、哪宫是用，理由）
・体用五行生克关系（相生/相克/比和，具体说明五行是什么）
・吉凶初判（用生体=吉/体克用=吉/体生用=泄/用克体=凶，给出明确结论）

三、三卦合参（每卦不少于200字）
・本卦象义：当前命局格局与性格特质深度解读
・互卦象义：中期变化趋势与潜在转折深度解读
・变卦象义：最终走向与人生后期格局深度解读

四、婚恋与富贵推断
・根据卦象的财富层次（给资产区间估算，说明哪个爻象支持此判断）
・根据卦象的婚姻走向（婚次/配偶特征，具体描述不少于150字）
・人生最大机遇期（给年龄段+说明哪个爻象对应）
・人生最大风险期（给年龄段+说明警示依据）

五、核心结论（一句话总结命格走向，直接）

六、卦象指示的可为与不可为
・3个「可为」时机（各给年龄段/年份区间 + 命理依据 + 具体操作建议）
・3个「不可为」时机（各给年龄段 + 具体风险说明 + 防范措施）`,
  },
  {
    key: 'heluo_detail', label: '卦象深析', icon: '象',
    getPrompt: () => DEPTH_PREFIX + `请对本人命盘的河洛易数卦象做深度爻辞解析，按以下结构详细输出，每爻不少于150字：

一、六爻逐爻分析（依据本卦六爻，逐一解析与命主人生阶段的对应）
初爻（0-15岁）：此阶段命运走向 / 关键影响因素 / 重要事件类型 / 父母与命主的互动模式
二爻（15-30岁）：此阶段发展方向 / 核心机遇类型 / 核心挑战类型 / 与学业/初职/初恋的关系
三爻（30-45岁）：此阶段是否为命格爆发期/转折期 / 事业财富的具体方向 / 婚姻稳定性
四爻（45-60岁）：此阶段能量走向 / 是收获期还是转型期 / 与子女/下属的关系
五爻（60-75岁）：晚年格局 / 财富保存状态 / 健康重点 / 晚年幸福度评估
上爻（75岁后）：命格收尾 / 身后影响力 / 子嗣缘分的最终呈现

二、动爻深析
・变动之爻代表的人生关键转折节点（给年龄区间+为什么这个爻动意味着转折）
・动爻前后卦象的对比（从本卦到变卦，人生格局发生了什么根本性改变）
・动爻对应的具体事件类型预测（财/婚/业/健各给一条预测）

三、经典爻辞引用与应期
・引用最相关的3条爻辞（每条完整引用原文）
・每条爻辞的应验年龄区间 + 对应现实事项预测（不少于100字）

四、吉凶时机判断
・最吉利的三个五年段（各给年龄区间 + 吉在何处 + 如何把握）
・最需谨慎的三个五年段（各给年龄区间 + 凶在何处 + 如何防范）
・趋吉避凶的3条具体行动指南（每条可操作，不抽象）

五、卦象总结（一句话，直接描述命运走向，诚实不客套）`,
  },
]

const QIMEN_MODES: ConsultMode[] = [
  {
    key: 'qimen_q1', label: '第一问：一生回顾', icon: '一',
    getPrompt: () => DEPTH_PREFIX + `请用奇门遁甲分析本命主一生格局，严格按以下结构详细输出：

【第一问：一生格局与过去事件回顾】

一、命盘格局判定
・值符落宫分析（具体说明：值符是哪颗星、落入哪宫、该宫的五行属性、对命主能量与贵人格局的具体影响，不少于150字）
・值使落宫分析（具体说明：值使是哪个门、落入哪宫、对命主行动模式与际遇类型的具体影响，不少于150字）
・两者组合的命格定性（强势/普通/弱势，给具体判断与3条理由）

二、吉凶格局分析
・三门三奇入中推演（具体说明命主最利的方位——东/南/西/北/东南等，最利行业类型）
・一生中贵人出现的规律（什么年龄段、什么类型的贵人、从哪个方向来）
・命局的核心障碍类型（具体说最容易遭遇的阻力来自哪类人、哪个领域，为什么）

三、过去十年具体事件回顾（必须给3个具体年份，每条不少于150字）
格式：XXXX年（干支年）[事件类型]
・流年干支与命局/大运的具体冲合关系分析
・奇门格局显示此年发生的具体事项描述（要有细节，不能笼统说"事业有变动"）
・此事件对命主的影响与长期意义

事件一（XXXX年，XX干支）：
事件二（XXXX年，XX干支）：
事件三（XXXX年，XX干支）：

四、命局核心议题
・一生的主旋律与核心命题（一句话，直接，不客套）
・命主最大的命运挑战是什么（具体说明，不泛泛而谈）
・破局关键在哪里（给具体可操作的方向，3条）

五、交叉验证
・给出2个可以验证本次奇门分析准确性的历史事件
（格式：年份 + 事件类型 + 奇门格局解释）`,
  },
  {
    key: 'qimen_q2', label: '第二问：大运机会', icon: '二',
    getPrompt: () => DEPTH_PREFIX + `请用奇门遁甲分析本命主当前大运的详细机会与风险，严格按以下结构详细输出：

【第二问：当前大运十年深析】

一、大运奇门格局
・大运干支入中后的星门宫位变化（具体说明：哪颗星落哪宫、哪个门落哪宫，不少于150字）
・大运值符/值使对命主能量的增减影响（逐一分析天干与地支的具体影响）
・这十年整体运势定性：顺运/逆运/先顺后逆（给明确判断 + 3条判断依据）

二、关键机会年份（必须列出2-3个，每个不少于200字）
格式：XXXX年（干支）
・当年奇门格局分析（星门宫组合）
・最值得抓的具体机遇（详细说明：是什么机遇、在哪个领域、如何出现）
・最优操作建议（具体可操作步骤，如"此年适合[X]，应在[Y]月[Z]行动"）

机会一（XXXX年）：
机会二（XXXX年）：
机会三（XXXX年，如有）：

三、最利发展方向
・最利方位（具体方位如东南/西北，解释奇门格局为何显示此方有利）
・最适合行业（给出2-3个具体行业，如"互联网电商"而非"做生意"，说明命理依据）
・财富爆发的最优策略（具体操作步骤，不抽象，给3条可执行建议）

四、最大风险年份
・具体风险年份（给干支）+ 风险类型（财/事/健/情）
・这一年可能发生什么（具体描述，不笼统）
・防范措施（具体的防范行动，给3条可执行建议）

五、大运核心建议（一句话，直接）

六、交叉验证
・给出2个可验证准确性的当前大运内已发生事件
（格式：年份 + 事件 + 奇门格局解释）`,
  },
  {
    key: 'qimen_q3', label: '第三问：具体事项', icon: '三',
    getPrompt: (extra = {}) => DEPTH_PREFIX + `请用奇门遁甲判断以下具体事项的成败，严格按以下结构详细输出：

【第三问：具体事项成败判断】

事项信息：
・时间：${extra['year'] || '[请在上方填写，如2025年乙巳]'}
・事情：${extra['event'] || '[请在上方填写，如投资创业/求职换工作/感情确认/置业买房]'}
・方向/对象：${extra['direction'] || '[请在上方填写，如向东南发展/合作对象姓X]'}

一、起局分析（不少于200字）
・流年干支的五行状态与日主命局的生克关系（具体分析：是相生还是相克，影响如何）
・流年大运双重叠加对该事项的综合影响（说明叠加后是利还是不利，理由各2条）
・当前命主的整体能量状态（强还是弱，利于主动出击还是守势待时）

二、事体宫状态（不少于200字）
・以事项类型确认用神宫位（财/官/婚等，说明确认方法与依据）
・用神宫的星门组合（落哪星+哪门，具体说明是吉星还是凶星，是吉门还是凶门）
・用神宫是否逢空亡/刑冲（有则说明影响，无则说明无）
・体用五行生克关系（吉/凶/平，说明理由）

三、合作方与外部环境（不少于150字）
・六合宫分析（合作对象/外部环境的能量状态，是助力还是阻力）
・是否有贵人助力格局（有则说明贵人来自哪个方向/领域/时间点）
・是否有小人阻碍格局（有则说明应规避的对象类型与时间节点）

四、最终结论
・可为/不可为（明确给出二选一，不得模棱两可）
・若可为：最佳操作时机（月份区间）+ 关键注意点（3条）+ 最优行动方案
・若不可为：具体原因（3条）+ 最好的替代方向（给出1-2个替代选项）
・禁忌方向/禁忌操作（明确列出3条，具体说明为什么禁忌）

五、交叉验证
・给出1个类似事项在命盘中有迹可循的历史验证
（格式：年份 + 类似事项 + 当时奇门格局对比说明）`,
  },
]

const currentModes = computed<ConsultMode[]>(() => {
  if (activeMethod.value === 'bazi')  return BAZI_MODES
  if (activeMethod.value === 'heluo') return HELUO_MODES
  return QIMEN_MODES
})

watch(activeMethod, (m) => {
  const map: Record<MethodKey, ConsultMode[]> = { bazi: BAZI_MODES, heluo: HELUO_MODES, qimen: QIMEN_MODES }
  activeSubMode.value = map[m][0].key
})

const currentMode = computed<ConsultMode | undefined>(() =>
  currentModes.value.find(m => m.key === activeSubMode.value),
)

const isQimenQ3 = computed(() => activeSubMode.value === 'qimen_q3')

async function launchConsult(): Promise<void> {
  const mode = currentMode.value
  if (!mode) return
  const extra: Record<string, string> = isQimenQ3.value
    ? { year: qimenExtra.value.year, event: qimenExtra.value.event, direction: qimenExtra.value.direction }
    : {}
  await evtConsult(mode.getPrompt(extra))
}
</script>

<template>
  <section class="card section-inline">
    <h2 class="card-title">年份事件</h2>

    <!-- 未保存提示 -->
    <div v-if="!caseId" class="yev-save-hint">
      <p class="muted">保存案例后可查看年份事件预测（婚姻 / 财运 / 置业 / 事业 / 健康）。</p>
      <button class="btn-primary" style="margin-top:8px" @click="emit('open-save-dialog')">保存案例 →</button>
    </div>

    <!-- 时间轴摘要 -->
    <div v-if="evtTrend" class="yev-trend-block">
      <p v-if="evtTimelineSummary" class="yev-timeline-summary">{{ evtTimelineSummary }}</p>
      <div class="yev-year-track">
        <div
          v-for="s in evtSummaries" :key="s.year"
          :class="['yev-year-chip', { 'yev-year-active': s.year === evtYear }]"
          @click="selectYear(s.year)"
        >
          <div class="yev-year-num">{{ s.year }}</div>
          <div class="yev-year-gz">{{ s.year_ganzhi }}</div>
          <div
            class="yev-year-score-bar"
            :style="{ height: Math.round(s.annual_score * 40 / 10) + 'px', minHeight: '4px' }"
            :class="s.annual_score >= 6 ? 'bar-good' : s.annual_score <= 3 ? 'bar-bad' : 'bar-mid'"
          ></div>
          <div class="yev-year-risk" :class="'risk-' + s.risk">{{ RISK_LABEL[s.risk] }}</div>
        </div>
      </div>
      <p v-if="evtTrendLoading" class="muted small">加载趋势中…</p>
    </div>
    <div v-else-if="evtTrendLoading" class="yev-loading">加载多年趋势中…</div>
    <div v-else-if="!evtTrend" class="yev-no-trend">
      <button class="btn-sec" @click="fetchTrend()">加载多年趋势</button>
    </div>

    <!-- 年份选择器 + 事件类型切换 -->
    <div class="yev-controls">
      <div class="yev-year-pick">
        <label>预测年份</label>
        <input
          type="number"
          :value="evtYear"
          min="2020" max="2060"
          @change="selectYear(Number(($event.target as HTMLInputElement).value))"
        />
      </div>
      <div class="yev-event-pills">
        <button
          v-for="et in ALL_EVENT_TYPES" :key="et"
          :class="['evt-pill', { 'evt-pill-active': evtType === et }]"
          @click="selectEventType(et)"
        >{{ EVENT_DISPLAY[et] }}</button>
      </div>
    </div>
    <p v-if="evtLoading" class="muted">分析中…</p>

    <!-- 事件结果卡 -->
    <div v-if="evtResult" class="yev-result-card">
      <div class="yev-result-header">
        <span class="yev-event-name">{{ EVENT_DISPLAY[evtType] }}</span>
        <span class="yev-gz">{{ evtData?.year_ganzhi }} 年</span>
        <span :class="['yev-risk-badge', 'risk-' + evtResult.risk_level]">风险：{{ RISK_LABEL[evtResult.risk_level] }}</span>
        <span :class="['yev-opp-badge', 'opp-' + evtResult.opportunity_level]">机遇：{{ RISK_LABEL[evtResult.opportunity_level] }}</span>
        <span class="yev-conf">置信 {{ Math.round(evtResult.confidence * 100) }}%</span>
      </div>
      <p class="yev-main-judgment">{{ evtResult.main_judgment }}</p>
      <p v-if="evtResult.trigger_summary" class="yev-trigger-summary">{{ evtResult.trigger_summary }}</p>

      <!-- 信号列表 -->
      <div v-if="evtResult.signals?.length" class="yev-signals">
        <div v-for="sig in evtResult.signals" :key="sig.signal_key" :class="['yev-sig-chip', 'layer-' + sig.layer]">
          <span class="sig-layer-lbl">{{ SIGNAL_LAYER_LABEL[sig.layer] }}</span>
          <span class="sig-label">{{ sig.label }}</span>
        </div>
      </div>

      <!-- 关键月份 -->
      <div v-if="evtResult.key_months?.length" class="yev-months">
        <span class="yev-months-lbl">关键月份：</span>
        <span v-for="m in evtResult.key_months" :key="m" class="yev-month-tag">{{ m }}月</span>
      </div>

      <!-- 可能表现 -->
      <div v-if="evtResult.possible_manifestations?.length" class="yev-list-block">
        <div class="yev-list-title">可能的现实表现</div>
        <ul class="yev-list">
          <li v-for="m in evtResult.possible_manifestations" :key="m">{{ m }}</li>
        </ul>
      </div>

      <!-- 预兆 -->
      <div v-if="evtResult.omens?.length" class="yev-list-block">
        <div class="yev-list-title">现实预兆</div>
        <ul class="yev-list">
          <li v-for="o in evtResult.omens" :key="o">{{ o }}</li>
        </ul>
      </div>

      <!-- 建议 -->
      <div v-if="evtResult.advice?.length" class="yev-list-block yev-advice">
        <div class="yev-list-title">应对建议</div>
        <ul class="yev-list">
          <li v-for="a in evtResult.advice" :key="a">{{ a }}</li>
        </ul>
      </div>

      <!-- 古籍依据 -->
      <div v-if="evtResult.classical_notes?.length" class="yev-classical">
        <span v-for="cn in evtResult.classical_notes" :key="cn.basis" class="yev-classical-note">
          {{ cn.source }}「{{ cn.basis }}」
        </span>
      </div>

      <!-- avoid_overclaim -->
      <div v-if="evtResult.avoid_overclaim" class="yev-overclaim">
        ⚠ {{ evtResult.avoid_overclaim }}
      </div>
    </div>
    <div v-else-if="!evtLoading && evtData" class="muted">暂无该事件分析结果</div>
    <div v-else-if="!evtLoading && !evtData && caseId" class="yev-empty">
      <button class="btn-sec" @click="fetchYearEvents()">分析 {{ evtYear }} 年事件</button>
    </div>

    <!-- AI 咨询区 -->
    <div v-if="evtResult" class="yev-consult-block">
      <div class="yev-consult-title">AI 深度咨询</div>
      <div class="yev-consult-input-row">
        <input
          v-model="evtUserQuestion"
          class="yev-consult-input"
          placeholder="输入你的问题，例如：今年婚姻有没有问题？"
          @keyup.enter="handleEvtConsult(evtUserQuestion)"
        />
        <button
          class="btn-primary yev-ask-btn"
          :disabled="evtConsultLoading || !evtUserQuestion.trim()"
          @click="handleEvtConsult(evtUserQuestion)"
        >{{ evtConsultLoading ? '解读中…' : '咨询' }}</button>
      </div>
      <!-- 追问问题 -->
      <div class="yev-followup-row">
        <button
          v-for="q in evtFollowups" :key="q"
          class="yev-followup-btn"
          @click="handleEvtConsult(q)"
        >{{ q }}</button>
      </div>
      <!-- 解读结果 -->
      <div v-if="evtConsultText" class="yev-consult-result">
        <pre class="yev-consult-pre">{{ evtConsultText }}</pre>
      </div>
      <p v-if="evtConsultError" class="error-msg">{{ evtConsultError }}</p>
    </div>

    <!-- ======= 三法深度 AI 咨询 ======= -->
    <div v-if="caseId" class="yev-methods-section">
      <div class="yev-methods-header">
        <span class="yev-methods-icon">🔮</span>
        <span class="yev-methods-title">深度命理分析</span>
        <span class="yev-methods-sub">三大命理体系 · 结构化深析</span>
      </div>

      <!-- 门派 Tab -->
      <div class="yev-method-tabs">
        <button
          v-for="m in METHODS" :key="m.key"
          :class="['yev-method-tab', { active: activeMethod === m.key }]"
          @click="activeMethod = (m.key as MethodKey)"
        >
          <span class="tab-label">{{ m.label }}</span>
          <span class="tab-desc">{{ m.desc }}</span>
        </button>
      </div>

      <!-- 子模式按钮 -->
      <div class="yev-submode-list">
        <button
          v-for="mode in currentModes" :key="mode.key"
          :class="['yev-submode-btn', { active: activeSubMode === mode.key }]"
          @click="activeSubMode = mode.key"
        >
          <span class="submode-icon">{{ mode.icon }}</span>
          <span class="submode-label">{{ mode.label }}</span>
        </button>
      </div>

      <!-- 奇门第三问额外输入 -->
      <div v-if="isQimenQ3" class="yev-qimen-extra">
        <div class="extra-row">
          <label>时间</label>
          <input v-model="qimenExtra.year" placeholder="如：2025年乙巳" />
        </div>
        <div class="extra-row">
          <label>事情</label>
          <input v-model="qimenExtra.event" placeholder="如：投资创业 / 求职换工作 / 感情确认" />
        </div>
        <div class="extra-row">
          <label>方向/对象</label>
          <input v-model="qimenExtra.direction" placeholder="如：向东南发展 / 合作对象姓X" />
        </div>
      </div>

      <!-- 发起按钮 -->
      <button class="yev-launch-btn" :disabled="evtConsultLoading" @click="launchConsult">
        <span v-if="evtConsultLoading">⏳ 分析中…</span>
        <span v-else>▶ 开始{{ currentMode?.label }}分析</span>
      </button>

      <!-- 分析结果 -->
      <div v-if="evtConsultText && !evtConsultLoading" class="yev-methods-result">
        <div class="methods-result-header">
          <span class="result-method-badge">{{ METHODS.find(m => m.key === activeMethod)?.label }}</span>
          <span class="result-mode-badge">{{ currentMode?.label }}</span>
        </div>
        <pre class="methods-result-pre">{{ evtConsultText }}</pre>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ─── 年份事件预测 ─────────────────────────────────────────── */
.yev-timeline-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-year-track { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); overflow-x: auto; padding-bottom: 4px; }
.yev-year-chip { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 10px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); background: var(--surface-2); min-width: 52px; transition: border-color 0.2s, background 0.2s; }
.yev-year-chip:hover { border-color: var(--accent); }
.yev-year-active { border-color: var(--accent) !important; background: color-mix(in srgb, var(--accent) 10%, var(--surface-2)) !important; }
.yev-year-num { font-size: var(--fs-xs); color: var(--text-2); }
.yev-year-gz { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.yev-year-score-bar { width: 24px; border-radius: 3px; margin: 2px 0; }
.bar-good { background: #4ade80; } .bar-bad { background: #f87171; } .bar-mid { background: #fbbf24; }
.yev-year-risk { font-size: 10px; }
.yev-controls { display: flex; align-items: center; gap: var(--sp-4); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.yev-year-pick { display: flex; align-items: center; gap: var(--sp-2); }
.yev-year-pick label { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; }
.yev-year-pick input { width: 80px; padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text); }
.yev-event-pills { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.evt-pill { padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-2); font-size: var(--fs-sm); color: var(--text-2); cursor: pointer; transition: all 0.15s; }
.evt-pill:hover { border-color: var(--accent); color: var(--text); }
.evt-pill-active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); font-weight: 600; }
.yev-result-card { border: 1px solid var(--border); border-radius: 12px; padding: var(--sp-4); margin-bottom: var(--sp-4); }
.yev-result-header { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-event-name { font-size: var(--fs-lg); font-weight: 700; color: var(--text); }
.yev-gz { font-size: var(--fs-sm); color: var(--text-2); }
.yev-risk-badge, .yev-opp-badge { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.risk-high { background: #fee2e2; color: #dc2626; }
.risk-medium_high { background: #fef3c7; color: #d97706; }
.risk-medium { background: #fef3c7; color: #ca8a04; }
.risk-low { background: #f0fdf4; color: #16a34a; }
.risk-none { background: var(--surface-2); color: var(--text-2); }
.opp-high { background: #d1fae5; color: #059669; }
.opp-medium_high { background: #d1fae5; color: #16a34a; }
.opp-medium { background: #ecfdf5; color: #22c55e; }
.opp-low { background: var(--surface-2); color: var(--text-2); }
.opp-none { background: var(--surface-2); color: var(--text-2); }
.yev-conf { font-size: var(--fs-xs); color: var(--text-2); margin-left: auto; }
.yev-main-judgment { font-size: var(--fs-md); color: var(--text); line-height: 1.6; margin-bottom: var(--sp-2); font-weight: 500; }
.yev-trigger-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-signals { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-sig-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); border: 1px solid var(--border); background: var(--surface-2); }
.layer-natal_base { border-color: #c4b5fd; background: #f5f3ff; }
.layer-dayun_trigger { border-color: #93c5fd; background: #eff6ff; }
.layer-liunian_trigger { border-color: #6ee7b7; background: #ecfdf5; }
.layer-month_trigger { border-color: #fde68a; background: #fffbeb; }
.sig-layer-lbl { font-size: 10px; color: var(--text-2); }
.sig-label { font-size: var(--fs-xs); color: var(--text); }
.yev-months { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: var(--sp-3); }
.yev-months-lbl { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; }
.yev-month-tag { padding: 2px 8px; background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); border-radius: 4px; font-size: var(--fs-xs); font-weight: 600; }
.yev-list-block { margin-bottom: var(--sp-3); }
.yev-list-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-1); }
.yev-list { margin: 0; padding-left: 1.2em; font-size: var(--fs-sm); color: var(--text); line-height: 1.7; }
.yev-advice .yev-list-title { color: var(--accent); }
.yev-classical { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: var(--sp-2); }
.yev-classical-note { margin-right: var(--sp-3); }
.yev-overclaim { font-size: var(--fs-xs); color: #d97706; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 6px 10px; margin-top: var(--sp-2); }
.yev-consult-block { margin-top: var(--sp-4); border-top: 1px solid var(--border); padding-top: var(--sp-4); }
.yev-consult-title { font-size: var(--fs-md); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); }
.yev-consult-input-row { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-consult-input { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); font-size: var(--fs-sm); }
.yev-consult-input:focus { outline: none; border-color: var(--accent); }
.yev-ask-btn { white-space: nowrap; }
.yev-followup-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-followup-btn { padding: 4px 12px; font-size: var(--fs-xs); border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); color: var(--text-2); cursor: pointer; transition: border-color 0.15s; }
.yev-followup-btn:hover { border-color: var(--accent); color: var(--text); }
.yev-consult-result { background: var(--surface-2); border-radius: 8px; padding: var(--sp-4); border: 1px solid var(--border); }
.yev-consult-pre { white-space: pre-wrap; word-break: break-word; font-family: var(--font-cn); font-size: var(--fs-sm); color: var(--text); line-height: 1.8; margin: 0; }
.yev-no-trend, .yev-empty { padding: var(--sp-4) 0; }
.yev-loading { color: var(--text-2); font-size: var(--fs-sm); padding: var(--sp-3) 0; }
.yev-save-hint {
  display: flex; flex-direction: column; align-items: flex-start;
  padding: var(--sp-3) var(--sp-4);
  background: color-mix(in srgb, var(--accent) 6%, var(--surface-2));
  border: 1px dashed var(--border);
  border-radius: 8px;
  margin-bottom: var(--sp-3);
}
.yev-save-hint p { margin: 0; font-size: var(--fs-sm); }
.yev-trend-block { margin-bottom: var(--sp-4); }
.section-inline { margin-bottom: var(--sp-5); }
.section-inline .card-title { font-size: var(--fs-xl); font-weight: 700; padding-bottom: var(--sp-3); border-bottom: 1px solid var(--border); margin-bottom: var(--sp-4); }

/* ===== 三法深度分析 ===== */
.yev-methods-section {
  margin-top: 2rem;
  border-top: 2px solid var(--border);
  padding-top: 1.5rem;
}
.yev-methods-header {
  display: flex; align-items: center; gap: .6rem;
  margin-bottom: 1.2rem;
}
.yev-methods-icon { font-size: 1.4rem; }
.yev-methods-title { font-size: 1.05rem; font-weight: 700; color: var(--text); }
.yev-methods-sub { font-size: .78rem; color: var(--text-2); margin-left: .2rem; }

/* 门派 Tab */
.yev-method-tabs {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: .6rem;
  margin-bottom: 1rem;
}
.yev-method-tab {
  display: flex; flex-direction: column; align-items: center;
  padding: .7rem .5rem; border-radius: 10px;
  border: 1.5px solid var(--border);
  background: var(--surface-2);
  cursor: pointer; transition: all .18s;
}
.yev-method-tab.active {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, var(--surface-2));
}
.tab-label { font-size: .92rem; font-weight: 700; color: var(--text); }
.tab-desc  { font-size: .68rem; color: var(--text-2); margin-top: .2rem; text-align: center; line-height: 1.3; }

/* 子模式按钮 */
.yev-submode-list {
  display: flex; flex-wrap: wrap; gap: .5rem;
  margin-bottom: 1rem;
}
.yev-submode-btn {
  display: flex; align-items: center; gap: .35rem;
  padding: .38rem .85rem; border-radius: 20px;
  border: 1.5px solid var(--border);
  background: transparent; cursor: pointer; transition: all .15s;
  font-size: .84rem; color: var(--text-2);
}
.yev-submode-btn.active {
  border-color: var(--accent);
  background: var(--accent); color: #fff;
}
.submode-icon {
  width: 1.3rem; height: 1.3rem; border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  display: flex; align-items: center; justify-content: center;
  font-size: .72rem; font-weight: 700; flex-shrink: 0;
}
.yev-submode-btn.active .submode-icon { background: rgba(255,255,255,.22); color: #fff; }
.submode-label { font-size: .84rem; }

/* 奇门第三问额外输入 */
.yev-qimen-extra {
  background: var(--surface-2); border-radius: 10px;
  padding: .9rem 1rem; margin-bottom: .9rem;
  display: flex; flex-direction: column; gap: .55rem;
  border: 1px solid var(--border);
}
.extra-row { display: flex; align-items: center; gap: .6rem; }
.extra-row label {
  min-width: 5rem; font-size: .82rem; font-weight: 600;
  color: var(--text-2); white-space: nowrap;
}
.extra-row input {
  flex: 1; padding: .32rem .65rem; border-radius: 7px;
  border: 1px solid var(--border);
  background: var(--surface-1, #fff); font-size: .84rem;
  color: var(--text);
}
.extra-row input:focus { outline: none; border-color: var(--accent); }

/* 发起按钮 */
.yev-launch-btn {
  width: 100%; padding: .72rem;
  background: var(--accent); color: #fff;
  border: none; border-radius: 10px; font-size: .96rem;
  font-weight: 700; cursor: pointer; transition: opacity .18s;
  margin-bottom: .8rem;
}
.yev-launch-btn:disabled { opacity: .55; cursor: not-allowed; }
.yev-launch-btn:not(:disabled):hover { opacity: .88; }

/* 分析结果 */
.yev-methods-result {
  border-radius: 12px;
  border: 1.5px solid var(--border);
  overflow: hidden;
}
.methods-result-header {
  display: flex; gap: .45rem; align-items: center;
  padding: .45rem .8rem;
  background: color-mix(in srgb, var(--accent) 8%, var(--surface-2));
  border-bottom: 1px solid var(--border);
}
.result-method-badge {
  padding: .18rem .55rem; border-radius: 11px;
  font-size: .76rem; font-weight: 700;
  background: var(--accent); color: #fff;
}
.result-mode-badge {
  padding: .18rem .55rem; border-radius: 11px;
  font-size: .76rem; font-weight: 600;
  background: color-mix(in srgb, var(--accent) 18%, var(--surface-2));
  color: var(--text);
}
.methods-result-pre {
  padding: 1rem 1.1rem; margin: 0;
  font-family: var(--font-cn); font-size: var(--fs-sm);
  line-height: 1.85; color: var(--text);
  white-space: pre-wrap; word-break: break-word;
  background: var(--surface-2);
  max-height: 600px; overflow-y: auto;
}
</style>
