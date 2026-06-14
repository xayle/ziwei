<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FlyingChartResponse } from '@/api/ziwei'
import { tfColorStyle } from '@/utils/ziweiViewHelpers'

type HuaType = '禄' | '权' | '科' | '忌'
type FilterKey = 'all' | 'lu' | 'quan' | 'ke' | 'ji'

const props = defineProps<{ flying: FlyingChartResponse }>()

// ── 讲解 Emit ─────────────────────────────────────────────
export interface FlyExplain {
  title: string
  subtitle: string
  huaColor: string
  body: string
  palaceDesc: string
}
const emit = defineEmits<{ (e: 'explain', v: FlyExplain): void }>()

// ── 筛选 ──────────────────────────────────────────────────
const filter = ref<FilterKey>('all')
const FILTER_TO_HUA: Record<Exclude<FilterKey, 'all'>, string> = {
  lu: '禄', quan: '权', ke: '科', ji: '忌',
}
/** 当前筛选的四化字符串，如"禄"；全部时为空字符串 */
const activeHua = computed<string>(() =>
  filter.value === 'all' ? '' : FILTER_TO_HUA[filter.value],
)

// ── 统计（fix Bug1: 遍历 keys "化禄"/"化权" 而非 values）──
const huaCounts = computed<Record<HuaType, number>>(() => {
  const c: Record<HuaType, number> = { '禄': 0, '权': 0, '科': 0, '忌': 0 }
  for (const p of (props.flying.palaces ?? [])) {
    for (const k of Object.keys(p.flying_out ?? {})) {
      for (const t of ['禄', '权', '科', '忌'] as HuaType[]) {
        if (k.includes(t)) c[t]++
      }
    }
  }
  return c
})

// ── 自化 ──────────────────────────────────────────────────
// self_transforms 格式: ["命宫宫干甲化禄自化", ...]
const selfHuaList = computed(() => {
  const all = props.flying.self_transforms ?? []
  return activeHua.value ? all.filter(s => s.includes(activeHua.value)) : all
})

// ── 飞出（按源宫分组）────────────────────────────────────
// flying_out keys = "化禄"/"化权"/"化科"/"化忌"
// flying_out values = "星名(落宫名)"，如 "天机(命宫)"
const emitGroups = computed(() =>
  (props.flying.palaces ?? [])
    .map(p => ({
      name: p.palace_name,
      stem: p.stem_name,
      items: Object.entries(p.flying_out ?? {})
        .filter(([k]) => !activeHua.value || k.includes(activeHua.value))
        .map(([huaK, target]) => ({ huaK, target })),
    }))
    .filter(g => g.items.length),
)

// ── 接收（fix Bug4: 后端预初始化12宫空数组，过滤之）────────
// received 格式: {宫名: ["命宫宫干甲化禄", ...]}
const receiveGroups = computed(() =>
  Object.entries(props.flying.received ?? {})
    .filter(([, items]) =>
      items.length && (!activeHua.value || items.some(s => s.includes(activeHua.value))),
    )
    .map(([palace, items]) => ({
      palace,
      items: activeHua.value ? items.filter(s => s.includes(activeHua.value)) : items,
    })),
)

// ── 冲宫（fix Bug4: 同上，过滤空数组）────────────────────
// chonged 格式: {宫名: ["命宫宫干甲化禄冲", ...]}
const chongGroups = computed(() =>
  Object.entries(props.flying.chonged ?? {})
    .filter(([, v]) =>
      v.length && (!activeHua.value || v.some(s => s.includes(activeHua.value))),
    )
    .map(([palace, items]) => ({
      palace,
      items: activeHua.value ? items.filter(s => s.includes(activeHua.value)) : items,
    })),
)

// ── 折叠状态（自化默认展开，其余收起）──────────────────────
const open = ref({ self: true, emit: false, receive: false, chong: false })
const activeKey = ref<string>('')

// ── 辅助：从描述字符串提取四化键，如 "化禄" ──────────────
function huaKey(s: string): string {
  for (const k of ['化禄', '化权', '化科', '化忌']) {
    if (s.includes(k)) return k
  }
  return ''
}

// ── 讲解相关常量与辅助 ────────────────────────────────────
const HUA_COLORS: Record<string, string> = {
  '禄': '#16a34a', '权': '#dc2626', '科': '#2563eb', '忌': '#7c3aed',
}
const PALACE_LONG: Record<string, string> = {
  '命宫': '自身气质、命运格局、外形体质与内心特质',
  '兄弟宫': '兄弟姐妹、挚友平辈、手足情缘与互助关系',
  '夫妻宫': '婚姻关系、感情伴侣、合伙事业与亲密互动',
  '子女宫': '子女运势、部下关系、创造才华与下一代缘分',
  '财帛宫': '财运走向、日常收支、金钱观念与理财能力',
  '疾厄宫': '身体状况、疾病倾向、意外风险与心理承压',
  '迁移宫': '出行运势、异地贵人、工作环境与社会际遇',
  '交友宫': '朋友人脉、贵人相助、竞争对手与社交圈质量',
  '官禄宫': '事业发展、官职名声、工作环境与职场竞争力',
  '田宅宫': '住宅房产、家庭环境、祖业遗产与居所质量',
  '福德宫': '心理状态、精神享乐、福气修为与内在满足感',
  '父母宫': '父母长辈、文书契约、上司贵人与学业文凭',
}
const HUA_EMIT_TIP: Record<string, (t: string) => string> = {
  '禄': t => `「化禄」主动飞入「${t}」，是命盘中最吉利的飞化格局之一。禄代表财气、福气与机遇，飞出意味着起宫将正向能量慷慨输送向「${t}」，令该宫所主的人、事、物顺遂充盈。起宫与「${t}」之间形成一条天然的能量补给线，无需外力推动，吉象自然流转。

落宫后的具体效应因「${t}」不同而异：落财帛则财路畅通、进项稳增；落官禄则贵人适时出现、事业顺势而升；落夫妻则感情温润、相处和谐；落疾厄则体质改善、病苦减轻。化禄之气的核心不在于「拥有」，而在于「流通」——能量在宫位之间流动，起宫因此相对消耗，而「${t}」则坐享其成。

整体而言为吉象，但需结合全局：若「${t}」同时有他宫忌射入或自化忌，则禄忌交战，吉中藏损；若起宫自身亦有忌气干扰，则所飞之禄成色不足。化禄飞出最怕「出门遇忌」，务必审查落宫及沿途宫位的整体四化状态，方能准确判断吉力的实际成色。`,
  '权': t => `「化权」主动飞入「${t}」，是命盘中力道最强的主动飞化之一。权代表掌控、主导、魄力与竞争欲；权气飞出，意味着起宫正以积极、强势、介入的方式向「${t}」输出影响力，推动该宫领域产生变化或提升其能量强度。

「${t}」受权气灌注后，事项会充满动感与张力：落事业宫则竞争力大增、易于拔尖；落夫妻宫则感情中出现主导或改变关系格局的驱动力；落财帛则积极追财、主动开源；落疾厄则体质趋于强健，但过度消耗亦需留意。权气之核心在于「驱动」，善用则成就卓越，过用则演变为固执或强权。

需注意：若权气落入受忌克制或主星落陷的宫位，则权力难以良性施展，反而化为冲突或内耗；若所飞宫位对应具体人物（如夫妻、父母），对方可能感受到命主强势介入而产生反弹。建议在「${t}」所主领域中有意识地以策略驾驭这股权力，而非让它成为无序的冲动能量。`,
  '科': t => `「化科」主动飞入「${t}」，是命盘中最温和、最持久的主动助力。科代表名誉、文书缘、认可与精神形象的提升；科气飞出，意味着起宫正以一种广受认可、提升声望的方式为「${t}」提供外部助益——它不强势、不张扬，但润物无声，长远有效。

「${t}」获科气加持后，在名声、文书、学习或社会评价方面将显著受益：落父母则文书契约顺利、上司认可；落官禄则在专业领域建立良好口碑、易获重用；落夫妻则伴侣形象佳、感情在旁观者眼中获肯定；落子女则子女有学艺加持或下属口碑良好。化科适合长线积累，对考试、资格认证、对外展示才华、签署合约等场景特别有利。

需留意：化科的性质是「被认可」而非「主动获取」，因此「${t}」所主领域中若命主能主动展示才华，方能将飞科的潜力转化为实际声誉资本；若一味内藏不露，科气亦可能悄然流散而未被世人知晓。形象的主动输出，是将此飞化变现的关键行动。`,
  '忌': t => `「化忌」主动飞入「${t}」，是命盘中最需高度关注的飞化格局。忌代表执着、遮蔽、耗损与纠缠；忌气飞出，意味着起宫正在向「${t}」输出负性压力，使该宫所主的人、事、物面临阻碍、牵制或受损。

「${t}」受忌气落入后，事项将可能经历重重困扰：落财帛则财务损耗、钱财难留；落夫妻则感情长期煎熬、伴侣带来困扰；落官禄则事业阻力重重、贵人难遇；落疾厄则体质消耗加速，须特别注意健康。重要的是，忌气从起宫主动飞来，说明起宫所代表的能量体是「${t}」困境的根源——找到源头，才能真正化解。

化忌不等于绝凶，它更像命盘中的放大镜，指向人生中最需用正念与行动修炼的领域。「${t}」所主之事往往也是命主执念最深之处，越执越被困。化解之道在于：直面「${t}」所主挑战，既不逃避也不执念，以实际行动化解束缚，将执念转化为深度成长的动力。`,
}
const HUA_RECV_TIP: Record<string, (s: string) => string> = {
  '禄': s => `「${s}」化禄射入本宫，是他宫向本宫馈赠财禄贵气的典型吉象。与起宫主动飞出不同，本宫此时处于「被滋养」的位置——「${s}」所代表的人物或能量体系，正主动为本宫所主事项提供外部资源与助力，是顺水行舟的天时之利，无需命主主动争取，吉气自然流入。

在实际生活中，此格局往往体现为：「${s}」所对应的人物（配偶、父母、兄弟、朋友等，因宫而异）在经济或情感上给予支持；或外部机遇、贵人垂青随之而至，使本宫事项顺利推进。这种来自外部的禄气比自化禄更稳固——自化禄散而难聚，而接收他宫之禄则有明确来源，更容易落实为看得见摸得着的益处，是真正的外力加持。

需留意「${s}」本身的状态是否健康：若「${s}」同时受忌气干扰，或「${s}」宫的主星落陷，则此禄气成色折损，吉力相应减弱。整体判断须审视「${s}」宫的四化全局——来源宫的质量直接决定飞入禄气的纯粹度。遇有瑕疵的禄射入，仍属吉象但需打折扣，同时关注该宫与本宫的互动模式是否健康。`,
  '权': s => `「${s}」化权射入本宫，外部权势之气主动注入，使本宫事项得到强力外部推动。此格局意味着「${s}」所代表的人物或机缘，正在主动介入本宫所主领域，以积极推动或强势影响的方式改变当前格局——命主无需全然依赖自身努力，有外力为其背书与加持。

在实际层面，往往体现为：外部贵人、长辈或机构（视「${s}」而定）主动介入并改变本宫走向——被推荐升职、被委以重任，或感情中对方主动追求。此类权气来自他宫，有外部背书，推动力通常比命主自身的主动更具影响力，可视为一种「外力驾驭本宫事项」的格局，恰当善用则事半功倍。

但需留意两面性：外来权气虽强，若本宫主星本身薄弱或有忌气，则外力难以完全发挥；同时权力介入也可能带来控制感或压力，使命主在本宫所主事项上失去部分自主性。建议在本宫所主领域借势而为，顺应这股外来推力，与其合作而非对抗，切忌逆势抵制而使吉力转为冲突。`,
  '科': s => `「${s}」化科射入本宫，来自外界的名誉助益与认可之气注入，是缓而有力的吉象。此格局意味着「${s}」所代表的人物或事机，正以提升名声、给予认可、帮助学习的方式惠及本宫所主的事项——这种助益不急不燥，润物无声，积累起来后往往比一时的禄权之气更加持久稳固，因为它改变的是外界对命主在本宫领域的评价与认知。

在生活中，这可能表现为：来自「${s}」对应关系的背书与推荐（上司赏识、长辈提携、贵人引荐）；文书证书类事项顺利推进；或与「${s}」相关的人在舆论评价上为命主加分。化科之气缓而绵长，不如禄财实在、不如权气强势，但在需要长期信誉积累的场合，往往是最可依赖的助力源。

尤以职场晋升、考试资格认定、社会声誉建设等事项最为应验。此射入科气是隐形的推力，需命主主动输出才华时方能倍增效果；若命主自身藏才不露，则外来科气虽好，也难以充分转化为实际的声誉与地位提升。`,
  '忌': s => `「${s}」化忌射入本宫，外部煞气主动侵扰，是飞化中最需谨慎对待的格局。此忌气来自「${s}」，代表该宫所对应的人物或力量体系正在消耗、拖累或干扰本宫所主的事项——无论命主是否察觉，这种耗损都在持续发生。因为源头在外，命主往往难以凭借主观意志轻易化解，反倒越努力越被牵绊。

具体表现因宫而异：若「${s}」为夫妻宫化忌射入财帛，伴侣的问题直接引发财务损耗；若为官禄化忌射入命宫，工作压力侵蚀命主身心；若为疾厄化忌射入福德，健康隐患令精神状态持续受累。忌气从外射来，命主主动控制的空间有限，因此最重要的是在「${s}」代表的领域提前布防、减少隐患，从源头切断忌气的生成与传递。

识别此格局的核心意义在于：很多时候人生某处的困境，根源并非当处本身的问题，而是来自「${s}」射入的忌气干扰。找到源头，回到「${s}」所主领域中寻求化解，才是真正的破局之道——头痛医头不治本，追溯飞忌来源、化解本源问题，方能从根本上解除本宫的压力。`,
}
const HUA_SELF_TIP: Record<string, (p: string) => string> = {
  '禄': p => `「${p}」宫干所化之禄落回本宫，命理上称「自化禄」，是一个颇具争议的特殊格局。表面上禄气大旺，实则如水中月、镜中花——禄气在宫内自产自销，一旦飞散便无影无踪，难以对外产生实质性的持续助力，更难变为命主手中可握的真实资源，是化禄中最难留住的形式。

在性格与行为层面，自化禄往往表现为：对「${p}」所主事项虽有热情，却缺乏长期坚持的耐力，来得快去得也快；财禄或情感得来容易、失去也快，或因过于随性而错失应当把握的机缘；处世潇洒有余、执行力略显不足，享受当下但难以为未来积累。尤其在财帛宫自化禄，主虽有财路但留不住钱，手头宽裕时容易随意消费，缺乏节制与积累意识。

应对之法：充分认识「禄气自散」的本质，主动以外部制度加以约束——强制储蓄计划、签署具有约束力的合约、或找一个能督促自己的外部结构，将禄气的潜力在逸散之前锁定为真实积累。切忌等待状态成熟、靠感觉行事，因为自化禄的本质就是「感觉很好但不留」，主动管理才是在此格局下积累资产的核心方法。`,
  '权': p => `「${p}」宫干化权落回本宫，命理上称「自化权」，是权气困于宫内、无法向外施展的格局。权气的本质是主导、行动、竞争与突破；然而自化后这股能量被限制在本宫内部循环，形成「内在极度强大，外部却难以形成威信」的矛盾状态，对外的实际影响力因此大打折扣。

在现实层面，自化权往往表现为：对「${p}」所主事项充满自信甚至自负，内心的想法和野心十分强烈，但实际上难以令他人信服或形成外部权威；行事容易独断专行、好大喜功、固执己见，或因情绪冲动损害原本可以顺利推进的事项；领导欲强却下属不服，掌控欲重却往往适得其反，与其说是有权威，不如说是在内耗自己。

改善之道：需刻意培养倾听与放权的能力，在「${p}」所主领域内学会适度示弱与分享控制权，将内在驱动力转化为有效的策略执行，而非陷入自我的权力闭环。借助合适的外部结构——团队、规则、组织架构——来承载和引导这股权气，其能量便可得到良性释放，从内在的强大真正转化为外部可见的成就。`,
  '科': p => `「${p}」宫干化科落回本宫，命理上称「自化科」，是才名之气困于内部、难以向外散播的格局。化科原本是助益名声与获得社会认可的吉星，自化后却如珠锁深匣——才情与口碑多在小圈子内流转，难以形成广泛的外部声誉，即使内行人了解实力，却始终无法「出圈」到更大的社会舞台。

在实际生活中，自化科的命主往往对「${p}」所主事项有出色见解与才华，圈内口碑也不差，但始终在能力展示上受限——通常习惯低调内秀，或有能力却严重缺乏主动展示的意愿与勇气；职场上的典型表现是：明明实力过硬，晋升却往往慢于同辈，时常有怀才不遇之感，但若追问是否主动表现过自己，往往答案是否定的。

破局之法：在「${p}」所主领域中，必须主动输出才华——公开发表观点、参与竞争展示、主动自我介绍、经营专业形象，都能帮助将自化飘散的科气凝聚为被社会认可的名誉资本。自化科的命主，缺的往往不是能力，而是让能力被看见的勇气与主动性。每一次主动「出圈」的行动，都是在对抗科气自散的桎梏，将潜在才华变为实际地位的关键步骤。`,
  '忌': p => `「${p}」宫干化忌落回本宫，命理上称「自化忌」，是命盘格局中较为严峻的组合——忌气困锁宫内，如阴云长期盘踞，持续耗损「${p}」所主领域的能量与资源。因为根源在宫位自身，这种消耗从内部生成，是一种深层的结构性困境，外部行动难以从根本上化解。

在性格与人生层面，自化忌往往带来深层执念：对「${p}」所主事物有近乎偏执的在意与失落感，欲壑难填、患得患失，即使表面风平浪静，内心深处始终有一块挥之不去的痛点与不安全感；会长期劳心费神于此宫所主领域，却又难以通过外部行动从根本解决——若在夫妻宫，感情中的自我消耗严重，越在乎越受伤；若在财帛宫，因焦虑主导财务决策、反而理财失当；若在命宫，内在的不安全感是贯穿一生的主题。

理解自化忌的关键在于：它是「内部问题」而非「外部打击」。面对此格局，向外寻找解决方案往往效果有限——换工作不解决命宫自化忌，换伴侣不解决夫妻宫自化忌。真正的化解之道在于向内探寻：正视这块心理软肋，从理解执念的来源开始，以成长与修炼逐步替代对「${p}」所主领域的执着，方是自化忌格局唯一真正有效的长期解法。`,
}
const HUA_CHONG_TIP: Record<string, (p: string) => string> = {
  '禄': p => `飞化落宫的对宫「${p}」因禄气流动而受到波及，产生命理上的「对宫感应」效应。在紫微斗数体系中，任何宫位发生飞化，其对宫必然感受到相应震动——此处并非「${p}」直接受惠于禄，而是受禄气流动所产生的间接影响：能量向飞化落宫方向倾斜，导致「${p}」在相对层面显得被弱化或忽视。

此种效应意味着「${p}」所代表的事项或人物，会因对面能量增强而相对产生位移：原本稳固的关系可能出现张弛，「${p}」的主导性与受关注度减弱，或命主在「${p}」所主事项上的精力与投入有所减少——因为命主的注意力与能量正在向飞化落宫的方向流动。禄气从对宫冲入，整体仍无大凶；可理解为「两宫之间能量的流动再分配」。

实际操作上：若飞化方向代表命主的主动意愿与追求，则「${p}」的被冲是这一追求所带来的必然代价——凡事有得必有失。需留意「${p}」宫的当事人（若宫主对应亲属或关系人）是否因此感到被忽视或冷落，及时沟通弥补关系为上策。理解禄冲对宫的本质，是一种提醒：在努力追求某事的同时，不要忘记照顾另一面。`,
  '权': p => `对宫「${p}」受权气所冲，是飞化冲宫中动能最强、影响最直接的效应之一。权气的本质是主导与争夺，当此气以飞化的形式落宫后，力量强势溢出并冲击对宫，「${p}」所主的领域会感受到来自飞化一方的巨大压力与介入——「${p}」的当事人或事项可能因此陷入被动、被制约或被迫调整的局面，两宫之间的权力张力显著增强。

在两性关系中，若命宫化权冲夫妻宫，往往意味着命主的强势性格严重影响伴侣的自主空间，或主导欲过强引发对方的反弹与对抗；若财帛宫化权冲田宅宫，财务决策可能对家庭不动产造成冲击；若官禄化权冲交友宫，职场竞争的能量蔓延至人脉圈，引发社交关系的张力。权气冲宫是主动一方能量溢出侵入对方领域，影响程度取决于「${p}」宫本身的护盾强度——主星落旺或有辅星守局则对冲力有一定抵御，反之冲力更烈。

应对此格局的关键在于主动管控：命主宜审视自身在飞化方向上是否施展了过度的权力，若「${p}」所代表的人物已呈现出反弹或受压信号，当适时收敛与调整，避免好事演变为强权控制，引发本可避免的对抗与冲突。主动与「${p}」所代表的领域和当事人沟通协商，而非单方面施压，方是上策。`,
  '科': p => `对宫「${p}」受科气所冲，是飞化冲宫中效应最为温和的一种格局。科气的本质是名誉与柔性助力，即便射冲对宫，力道也以影响形象评价、促成信息共振为主，较少引发激烈的宫位博弈，整体仍属轻吉或中性偏稳，不需过分担忧。

具体而言，「${p}」所主的领域可能因此受到来自飞化方的名声波及与影响：若官禄宫化科冲夫妻宫，职场声誉改变影响伴侣或合作关系对命主的评价；若父母宫化科冲子女宫，学业与文书能量间接惠及子女之学艺发展；若命宫化科冲迁移宫，个人形象的提升带动外出运及异地际遇的质量改善。科气冲宫有时甚至产生正向共振——使两宫之间的文化与评价信息流通更为顺畅，形成互相增益的良性效果。

唯需留意：名誉性事件（口碑、文书内容、资格认定）会在「${p}」所主的关系或事项中引发回响，其质量直接取决于命主自身形象是否内外一致、言行是否统一。若飞化方向有所失信或形象受损，则科气的波及可能使「${p}」所代表的关系或领域也受到评价上的负面影响，保持形象的真实性与一致性是最佳的防护。`,
  '忌': p => `对宫「${p}」遭忌气所冲，是命盘飞化中最需谨慎解读的冲宫格局之一。飞化落宫本已承受忌气的直接压迫，对宫「${p}」则受到此忌气的对冲波及——两宫双重共鸣，命主在飞化所涉及的两个人生领域同时承压，能量呈双向消耗状态，凶意较重，是命盘中须重点关注的不利组合。

在具体表现上，「${p}」所代表的人或事项往往像是被拖入一场本不属于自己的困局：可能遭受命主能量低谷期的间接波及，或因飞化方的麻烦延伸至「${p}」领域，使原本稳定的事项也出现动荡与损耗。典型案例：夫妻宫化忌冲命宫，配偶问题持续压迫命主身心；财帛宫化忌冲田宅，财务持续紧张波及家居不动产的稳定；官禄化忌冲交友，事业困境殃及人脉关系的质量与深度。

解读此格局须整体衡量：「${p}」宫是否有吉星或辅星坐守以抵消冲力？是否有来自其他宫位的禄、科来解救？若无任何化解，则在对应人生阶段须特别留意两宫所涉领域的双重风险。提前做好心理与物质两方面的防范预案，并尽量避免在两宫同时承压时做重大决策，等待格局转换的有利时机，才是应对此凶象的稳健策略。`,
}

function parseFlyTarget(target: string): { star: string; palace: string } {
  const m = target.match(/^(.+)\((.+)\)$/)
  return m ? { star: m[1], palace: m[2] } : { star: target, palace: '' }
}
function parsePalaceFromRaw(s: string): string {
  return s.match(/^([\u4e00-\u9fa5]{2,4}宫)/)?.[1] ?? ''
}

function onClickEmit(sourcePalace: string, huaK: string, target: string): void {
  const hua = huaK.slice(1)
  const landing = parseFlyTarget(target)
  const key = `emit-${sourcePalace}-${huaK}`
  if (activeKey.value === key) { activeKey.value = ''; return }
  activeKey.value = key
  emit('explain', {
    title: `${sourcePalace} 化${hua} → ${landing.palace || target}`,
    subtitle: landing.star ? `落星：${landing.star}` : '飞出落宫',
    huaColor: HUA_COLORS[hua] ?? '#888',
    body: HUA_EMIT_TIP[hua]?.(landing.palace || target) ?? '',
    palaceDesc: landing.palace ? `【${landing.palace}主】${PALACE_LONG[landing.palace] ?? ''}` : '',
  })
}
function onClickSelf(raw: string): void {
  const hk = huaKey(raw)
  const hua = hk.slice(1)
  const palace = parsePalaceFromRaw(raw)
  const key = `self-${raw}`
  if (activeKey.value === key) { activeKey.value = ''; return }
  activeKey.value = key
  emit('explain', {
    title: `${palace} 自化${hua}`,
    subtitle: '化气落回本宫・自旋散逸',
    huaColor: HUA_COLORS[hua] ?? '#888',
    body: HUA_SELF_TIP[hua]?.(palace) ?? '',
    palaceDesc: `【${palace}主】${PALACE_LONG[palace] ?? ''}`,
  })
}
function onClickReceive(targetPalace: string, raw: string): void {
  const hk = huaKey(raw)
  const hua = hk.slice(1)
  const srcPalace = parsePalaceFromRaw(raw)
  const key = `recv-${targetPalace}-${raw}`
  if (activeKey.value === key) { activeKey.value = ''; return }
  activeKey.value = key
  emit('explain', {
    title: `${targetPalace} 接收 化${hua}`,
    subtitle: srcPalace ? `来自 ${srcPalace}` : '他宫飞入',
    huaColor: HUA_COLORS[hua] ?? '#888',
    body: HUA_RECV_TIP[hua]?.(srcPalace) ?? '',
    palaceDesc: `【${targetPalace}主】${PALACE_LONG[targetPalace] ?? ''}`,
  })
}
function onClickChong(targetPalace: string, raw: string): void {
  const hk = huaKey(raw)
  const hua = hk.slice(1)
  const srcPalace = parsePalaceFromRaw(raw)
  const key = `chong-${targetPalace}-${raw}`
  if (activeKey.value === key) { activeKey.value = ''; return }
  activeKey.value = key
  emit('explain', {
    title: `${targetPalace} 被冲宫`,
    subtitle: srcPalace ? `因 ${srcPalace} 飞化所致` : '对冲牵连',
    huaColor: HUA_COLORS[hua] ?? '#888',
    body: HUA_CHONG_TIP[hua]?.(targetPalace) ?? '',
    palaceDesc: `【${targetPalace}主】${PALACE_LONG[targetPalace] ?? ''}`,
  })
}
</script>

<template>
  <!-- ══ 统计卡 + 筛选 ════════════════════════════════════════ -->
  <div class="stats-card">
    <div class="hua-counts">
      <div class="hua-stat hua-lu">
        <span class="hs-label">禄</span><span class="hs-num">{{ huaCounts['禄'] }}</span>
      </div>
      <div class="hua-stat hua-quan">
        <span class="hs-label">权</span><span class="hs-num">{{ huaCounts['权'] }}</span>
      </div>
      <div class="hua-stat hua-ke">
        <span class="hs-label">科</span><span class="hs-num">{{ huaCounts['科'] }}</span>
      </div>
      <div class="hua-stat hua-ji">
        <span class="hs-label">忌</span><span class="hs-num">{{ huaCounts['忌'] }}</span>
      </div>
      <div class="hua-stat hua-self">
        <span class="hs-label">自化</span>
        <span class="hs-num">{{ flying.self_transforms?.length ?? 0 }}</span>
      </div>
      <div class="hua-stat hua-recv">
        <span class="hs-label">接收</span>
        <span class="hs-num">{{ receiveGroups.length }}</span>
      </div>
    </div>
    <div class="filter-row">
      <span class="filter-label">筛选：</span>
      <button :class="['ff-btn', { active: filter === 'all' }]" @click="filter = 'all'">全部</button>
      <button :class="['ff-btn ff-lu', { active: filter === 'lu' }]" @click="filter = 'lu'">禄</button>
      <button :class="['ff-btn ff-quan', { active: filter === 'quan' }]" @click="filter = 'quan'">权</button>
      <button :class="['ff-btn ff-ke', { active: filter === 'ke' }]" @click="filter = 'ke'">科</button>
      <button :class="['ff-btn ff-ji', { active: filter === 'ji' }]" @click="filter = 'ji'">忌</button>
    </div>
  </div>
  <p class="click-hint">点击任意条目查看讲解 →</p>

  <!-- ══ 自化 ↺ ════════════════════════════════════════════════ -->
  <div class="fly-section">
    <div class="sec-header" @click="open.self = !open.self">
      <span class="sec-icon">↺</span>
      <span class="sec-title">自化</span>
      <span class="sec-count">{{ selfHuaList.length }}</span>
      <span class="sec-chevron" :class="{ rotated: open.self }">▼</span>
    </div>
    <div v-show="open.self" class="sec-body">
      <div v-if="selfHuaList.length" class="fly-tag-list">
        <span
          v-for="s in selfHuaList"
          :key="s"
          class="fly-tag clickable"
          :class="{ 'tag-active': activeKey === `self-${s}` }"
          :style="tfColorStyle(huaKey(s))"
          :title="'点击查看讲解'"
          @click="onClickSelf(s)"
        >{{ s }}</span>
      </div>
      <p v-else class="fly-empty">无自化</p>
    </div>
  </div>

  <!-- ══ 飞出 → ════════════════════════════════════════════════ -->
  <div class="fly-section">
    <div class="sec-header" @click="open.emit = !open.emit">
      <span class="sec-icon">→</span>
      <span class="sec-title">飞出（本宫化出）</span>
      <span class="sec-count">{{ emitGroups.reduce((n, g) => n + g.items.length, 0) }} 条</span>
      <span class="sec-chevron" :class="{ rotated: open.emit }">▼</span>
    </div>
    <div v-show="open.emit" class="sec-body">
      <div v-if="emitGroups.length" class="group-list">
        <div v-for="g in emitGroups" :key="g.name" class="palace-group">
          <div class="pg-head">
            <span class="pg-name">{{ g.name }}</span>
            <span v-if="g.stem" class="pg-stem">{{ g.stem }}干</span>
          </div>
          <div class="pg-items">
            <div
              v-for="item in g.items"
              :key="item.huaK"
              class="fly-row clickable"
              :class="{ 'row-active': activeKey === `emit-${g.name}-${item.huaK}` }"
              @click="onClickEmit(g.name, item.huaK, item.target)"
            >
              <span class="fly-badge" :style="tfColorStyle(item.huaK)">{{ item.huaK.slice(1) }}</span>
              <span class="fly-arrow">→</span>
              <span class="fly-target">{{ item.target }}</span>
              <span class="fly-hint">点击讲解</span>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="fly-empty">无符合条件的飞出</p>
    </div>
  </div>

  <!-- ══ 接收 ← ════════════════════════════════════════════════ -->
  <div class="fly-section">
    <div class="sec-header" @click="open.receive = !open.receive">
      <span class="sec-icon">←</span>
      <span class="sec-title">接收（他宫化入）</span>
      <span class="sec-count">{{ receiveGroups.length }} 宫</span>
      <span class="sec-chevron" :class="{ rotated: open.receive }">▼</span>
    </div>
    <div v-show="open.receive" class="sec-body">
      <div v-if="receiveGroups.length" class="group-list">
        <div v-for="g in receiveGroups" :key="g.palace" class="palace-group">
          <div class="pg-head">
            <span class="pg-name">{{ g.palace }}</span>
            <span class="pg-badge-count">{{ g.items.length }} 飞入</span>
          </div>
          <div class="pg-items">
            <div
              v-for="s in g.items"
              :key="s"
              class="fly-row clickable"
              :class="{ 'row-active': activeKey === `recv-${g.palace}-${s}` }"
              @click="onClickReceive(g.palace, s)"
            >
              <span class="fly-badge" :style="tfColorStyle(huaKey(s))">{{ huaKey(s).slice(1) || '?' }}</span>
              <span class="fly-arrow">←</span>
              <span class="fly-target" :title="s">{{ s }}</span>
              <span class="fly-hint">点击讲解</span>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="fly-empty">无符合条件的接收</p>
    </div>
  </div>

  <!-- ══ 冲宫 ⇄ ════════════════════════════════════════════════ -->
  <div class="fly-section">
    <div class="sec-header" @click="open.chong = !open.chong">
      <span class="sec-icon">⇄</span>
      <span class="sec-title">冲宫关系</span>
      <span class="sec-count">{{ chongGroups.length }} 宫</span>
      <span class="sec-chevron" :class="{ rotated: open.chong }">▼</span>
    </div>
    <div v-show="open.chong" class="sec-body">
      <div v-if="chongGroups.length" class="group-list">
        <div v-for="g in chongGroups" :key="g.palace" class="palace-group">
          <div class="pg-head">
            <span class="pg-name">{{ g.palace }}</span>
            <span class="pg-badge-count">被冲 {{ g.items.length }} 次</span>
          </div>
          <div class="pg-items">
            <div
              v-for="s in g.items"
              :key="s"
              class="fly-row clickable"
              :class="{ 'row-active': activeKey === `chong-${g.palace}-${s}` }"
              @click="onClickChong(g.palace, s)"
            >
              <span class="fly-badge" :style="tfColorStyle(huaKey(s))">{{ huaKey(s).slice(1) || '冲' }}</span>
              <span class="fly-arrow">⇄</span>
              <span class="fly-target" :title="s">{{ s }}</span>
              <span class="fly-hint">点击讲解</span>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="fly-empty">无符合条件的冲宫</p>
    </div>
  </div>
</template>

<style scoped>
/* ── 统计卡 ───────────────────────────────────────────────── */
.stats-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.hua-counts { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.hua-stat {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: var(--fs-sm);
  font-weight: 600;
}
.hs-label { font-weight: 700; }
.hua-lu   { background: #f0fdf4; border-color: #86efac; color: #166534; }
.hua-quan { background: #fff1f2; border-color: #fca5a5; color: #991b1b; }
.hua-ke   { background: #eff6ff; border-color: #93c5fd; color: #1e40af; }
.hua-ji   { background: #f5f3ff; border-color: #c4b5fd; color: #5b21b6; }
.hua-self { background: var(--surface); border-color: var(--border); color: var(--text-2); }
.hua-recv { background: var(--surface); border-color: var(--border); color: var(--text-2); }
.filter-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.filter-label { font-size: var(--fs-sm); color: var(--text-2); }
.ff-btn {
  padding: 4px 11px;
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.ff-btn:hover { border-color: var(--accent); color: var(--accent); }
.ff-btn.active  { background: var(--accent); color: #fff; border-color: var(--accent); }
.ff-lu.active   { background: #16a34a !important; border-color: #16a34a !important; }
.ff-quan.active { background: #dc2626 !important; border-color: #dc2626 !important; }
.ff-ke.active   { background: #2563eb !important; border-color: #2563eb !important; }
.ff-ji.active   { background: #7c3aed !important; border-color: #7c3aed !important; }

/* ── 折叠卡片 ─────────────────────────────────────────────── */
.fly-section {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
  overflow: hidden;
}
.sec-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  cursor: pointer;
  user-select: none;
  transition: background 0.12s;
}
.sec-header:hover { background: var(--surface-3, #f1f5f9); }
.sec-icon  { font-size: var(--fs-base); width: 20px; text-align: center; flex-shrink: 0; }
.sec-title { flex: 1; font-size: var(--fs-base); font-weight: 600; color: var(--text); font-family: var(--font-cn); }
.sec-count {
  font-size: var(--fs-xs);
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-2);
}
.sec-chevron { font-size: 10px; color: var(--text-2); transition: transform 0.2s; }
.sec-chevron.rotated { transform: rotate(180deg); }
.sec-body { padding: var(--sp-3) var(--sp-4); background: var(--surface); }

/* ── 自化标签 ──────────────────────────────────────────────── */
.fly-tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.fly-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: var(--fs-xs);
  font-weight: 500;
  color: #fff;
  cursor: default;
}
.fly-tag.clickable { cursor: pointer; }
.fly-tag.tag-active { outline: 3px solid #fff; box-shadow: 0 0 0 5px rgba(0,0,0,.25); }
.click-hint { font-size: var(--fs-xs); color: var(--text-3); margin: 0 0 var(--sp-3); }

/* ── 分组列表（飞出 / 接收 / 冲宫）─────────────────────────── */
.group-list { display: flex; flex-direction: column; gap: var(--sp-2); }
.palace-group { border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.pg-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 6px var(--sp-3);
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
}
.pg-name { font-size: var(--fs-sm); font-weight: 700; font-family: var(--font-cn); }
.pg-stem { font-size: var(--fs-xs); color: var(--text-2); }
.pg-badge-count {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 999px;
}
.pg-items { display: flex; flex-direction: column; gap: 4px; padding: var(--sp-2) var(--sp-3); }
.fly-row {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 6px; border-radius: var(--radius-sm); transition: background 0.12s;
}
.fly-row.clickable { cursor: pointer; }
.fly-row.clickable:hover { background: var(--surface-2); }
.fly-row.row-active { background: var(--surface-3, #f0f9ff); outline: 1px solid var(--accent); }
.fly-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: var(--fs-xs);
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.fly-arrow { color: var(--text-2); font-weight: 700; flex-shrink: 0; font-size: var(--fs-sm); }
.fly-target { color: var(--text); font-size: var(--fs-sm); font-family: var(--font-cn); flex: 1; }
.fly-hint { font-size: 10px; color: var(--text-3); opacity: 0; transition: opacity 0.15s; margin-left: auto; }
.fly-row.clickable:hover .fly-hint { opacity: 1; }
.fly-empty { font-size: var(--fs-sm); color: var(--text-3); margin: 0; }
</style>