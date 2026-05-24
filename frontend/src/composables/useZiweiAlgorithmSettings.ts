import { computed, ref } from 'vue'

type LeapMethod = 'mid' | 'next' | 'same'
type KuiyueMethod = 'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'
type TianmaMethod = 'year' | 'month'
type TiankongMethod = 'standard' | 'shun'
type BrightnessMethod = 'standard' | 'zhongzhou' | 'mod1' | 'mod2'
type JiukongMethod = 'dual' | 'single' | 'zhanyan'
type TianshangMethod = 'standard' | 'zhongzhou'
type MingzhuMethod = 'quanshu' | 'zhongzhou'
type LiunianSihuaMethod = 'year_stem' | 'life_palace_stem'
type ChangshengMethod = 'standard' | 'water_earth' | 'fire_earth'
type AlgoPreset = 'sanhe' | 'feixing' | 'qintian' | 'zhongzhou'

export function useZiweiAlgorithmSettings() {
  const showAlgoSettings = ref(false)
  const algoLateZishi = ref<boolean>(true)
  const algoLeapMethod = ref<LeapMethod>('mid')
  const algoKuiyue = ref<KuiyueMethod>('standard')
  const algoTianma = ref<TianmaMethod>('year')
  const algoTiankong = ref<TiankongMethod>('standard')
  const algoBrightness = ref<BrightnessMethod>('standard')
  const algoJiukong = ref<JiukongMethod>('dual')
  const algoTianshang = ref<TianshangMethod>('standard')
  const algoMingzhu = ref<MingzhuMethod>('quanshu')
  const algoLiunianSihua = ref<LiunianSihuaMethod>('life_palace_stem')
  const algoChangsheng = ref<ChangshengMethod>('standard')

  const sihuaJia = ref(0)
  const sihuaWu = ref(0)
  const sihuaGeng = ref(0)
  const sihuaXin = ref(0)
  const sihuaRen = ref(0)
  const sihuaGui = ref(0)

  function buildSihuaIndices(): Record<string, number> | undefined {
    const mapping: Record<string, number> = {}
    if (sihuaJia.value) mapping['甲'] = sihuaJia.value
    if (sihuaWu.value) mapping['戊'] = sihuaWu.value
    if (sihuaGeng.value) mapping['庚'] = sihuaGeng.value
    if (sihuaXin.value) mapping['辛'] = sihuaXin.value
    if (sihuaRen.value) mapping['壬'] = sihuaRen.value
    if (sihuaGui.value) mapping['癸'] = sihuaGui.value
    return Object.keys(mapping).length ? mapping : undefined
  }

  function resetAlgoSettings() {
    algoLateZishi.value = true
    algoLeapMethod.value = 'mid'
    algoKuiyue.value = 'standard'
    sihuaJia.value = sihuaWu.value = sihuaGeng.value = 0
    sihuaXin.value = sihuaRen.value = sihuaGui.value = 0
    algoTianma.value = 'year'
    algoTiankong.value = 'standard'
    algoBrightness.value = 'standard'
    algoJiukong.value = 'dual'
    algoTianshang.value = 'standard'
    algoMingzhu.value = 'quanshu'
    algoLiunianSihua.value = 'life_palace_stem'
    algoChangsheng.value = 'standard'
  }

  function applyPreset(preset: AlgoPreset) {
    resetAlgoSettings()
    switch (preset) {
      case 'sanhe':
        break
      case 'feixing':
        algoLeapMethod.value = 'next'
        algoTianma.value = 'month'
        algoBrightness.value = 'mod1'
        break
      case 'qintian':
        algoLateZishi.value = false
        algoLeapMethod.value = 'same'
        algoKuiyue.value = 'gengxin_mahu'
        sihuaGeng.value = 2
        algoJiukong.value = 'zhanyan'
        break
      case 'zhongzhou':
        algoBrightness.value = 'zhongzhou'
        algoTianshang.value = 'zhongzhou'
        algoMingzhu.value = 'zhongzhou'
        break
    }
  }

  const hasCustomAlgoSettings = computed(() => (
    !algoLateZishi.value ||
    algoLeapMethod.value !== 'mid' ||
    algoKuiyue.value !== 'standard' ||
    sihuaJia.value || sihuaWu.value || sihuaGeng.value || sihuaXin.value || sihuaRen.value || sihuaGui.value ||
    algoTianma.value !== 'year' ||
    algoTiankong.value !== 'standard' ||
    algoBrightness.value !== 'standard' ||
    algoJiukong.value !== 'dual' ||
    algoTianshang.value !== 'standard' ||
    algoMingzhu.value !== 'quanshu' ||
    algoLiunianSihua.value !== 'life_palace_stem' ||
    algoChangsheng.value !== 'standard'
  ))

  return {
    showAlgoSettings,
    algoLateZishi,
    algoLeapMethod,
    algoKuiyue,
    algoTianma,
    algoTiankong,
    algoBrightness,
    algoJiukong,
    algoTianshang,
    algoMingzhu,
    algoLiunianSihua,
    algoChangsheng,
    sihuaJia,
    sihuaWu,
    sihuaGeng,
    sihuaXin,
    sihuaRen,
    sihuaGui,
    hasCustomAlgoSettings,
    buildSihuaIndices,
    resetAlgoSettings,
    applyPreset,
  }
}
