/**
 * 八字规则引擎 flags（snake_case）→ 界面中文标签。
 * 来源：data/bazi_rules.json；未知 key 不回显英文原文。
 */
export const BAZI_RULE_FLAG_LABELS: Record<string, string> = {
  academic_achievement: '学业有成',
  academic_star: '文昌星',
  academic_talent: '学业天赋',
  auspicious: '吉利',
  auspicious_shensha: '吉神护持',
  authority_apt: '官贵倾向',
  autumn_energy: '秋令之气',
  benefactor_star: '贵人星',
  benefactors: '贵人相助',
  brave: '勇毅',
  brave_decisive: '果敢决断',
  brilliant_mind: '才思敏捷',
  broken_geju: '格局破格',
  buried_talent: '才不外露',
  career_instability: '事业起伏',
  career_talent: '事业天赋',
  center_direction: '居中方位',
  comfortable_life: '生活安稳',
  commercial_talent: '商业天赋',
  competitive: '好胜进取',
  competitive_spirit: '竞争意识',
  creative: '富创造力',
  cultural_talent: '文才出众',
  east_direction: '东方方位',
  expressive: '善于表达',
  favor_earth: '喜用土',
  favor_fire: '喜用火',
  favor_metal: '喜用金',
  favor_water: '喜用水',
  favor_wood: '喜用木',
  gentle_authority: '柔中带刚',
  happy_marriage: '婚姻和美',
  high_achievement: '成就较高',
  inner_excellence: '内蕴深厚',
  intelligent_unconventional: '聪明不羁',
  intuitive: '直觉敏锐',
  kill_seal_harmony: '杀印相生',
  late_bloomer: '大器晚成',
  law_finance_apt: '法金倾向',
  leadership: '领导力',
  literary_talent: '文采出众',
  loyal_marriage: '婚姻忠贞',
  lucky_support: '吉助加身',
  metal_water_talent: '金水聪颖',
  military_apt: '武职倾向',
  mobility: '走动活跃',
  need_adversity: '需经磨砺',
  need_remedy: '需调候补救',
  noble_destiny: '贵气命格',
  north_direction: '北方方位',
  notable_achievement: '功名可期',
  official_scholar: '官学双美',
  power_authority: '权柄较显',
  reliable: '为人可靠',
  resilient: '坚韧耐挫',
  restrained_talent: '才藏于内',
  risk_prone: '风险偏高',
  scholarly: '好学文气',
  self_reliance: '自立自强',
  sharp_mind: '心思敏锐',
  social_network: '人脉广布',
  south_direction: '南方方位',
  specialized_skill: '专长突出',
  spring_energy: '春令之气',
  stable_career: '事业稳健',
  stable_energy: '气势平稳',
  steady_wealth: '财运稳健',
  strong_will: '意志坚定',
  strong_willpower: '意志力强',
  summer_energy: '夏令之气',
  talent_authority: '才官相济',
  talent_wealth: '才财相生',
  team_player: '善于协作',
  travel_prone: '宜动宜行',
  unconventional_wisdom: '奇思睿智',
  variable_fortune: '运程起伏',
  versatile: '多才多艺',
  volatile_fortune: '运势多变',
  wealth_talent: '财才俱备',
  wealth_variety: '财源多样',
  well_rounded: '才艺周全',
  west_direction: '西方方位',
  winter_energy: '冬令之气',
  wood_fire_brilliance: '木火通明',
}

/** 将规则 flags 转为中文；未知英文 key 跳过，避免界面漏出 snake_case。 */
export function formatBaziRuleFlags(flags: string[] | undefined | null): string[] {
  if (!flags?.length) return []
  const labels: string[] = []
  for (const flag of flags) {
    const key = flag?.trim()
    if (!key) continue
    const label = BAZI_RULE_FLAG_LABELS[key]
    if (label) labels.push(label)
  }
  return labels
}

/** 命中条展示：规则中文名 + 可选中文语义标签 */
export function formatBaziRuleMatchLine(item: {
  name?: string | null
  flags?: string[] | null
}): string {
  const name = item.name?.trim() || ''
  const flagText = formatBaziRuleFlags(item.flags).join('、')
  if (name && flagText) return `${name}：${flagText}`
  return name || flagText
}
