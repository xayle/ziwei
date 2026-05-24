<script setup lang="ts">
/**
 * ZiweiAlgoSettings.vue — 安星算法设置折叠面板
 *
 * 通过 v-model 绑定各算法设置项；父组件直接传入来自
 * useZiweiAlgorithmSettings() 的响应式状态。
 */
defineProps<{
  showAlgoSettings:    boolean
  hasCustomAlgoSettings: boolean
  algoLateZishi:       boolean
  algoLeapMethod:      string
  algoKuiyue:          string
  algoTianma:          string
  algoTiankong:        string
  algoBrightness:      string
  algoJiukong:         string
  algoTianshang:       string
  algoMingzhu:         string
  algoLiunianSihua:    string
  algoChangsheng:      string
  sihuaJia:  number
  sihuaWu:   number
  sihuaGeng: number
  sihuaXin:  number
  sihuaRen:  number
  sihuaGui:  number
}>()

const emit = defineEmits<{
  'update:showAlgoSettings':  [v: boolean]
  'update:algoLateZishi':     [v: boolean]
  'update:algoLeapMethod':    [v: string]
  'update:algoKuiyue':        [v: string]
  'update:algoTianma':        [v: string]
  'update:algoTiankong':      [v: string]
  'update:algoBrightness':    [v: string]
  'update:algoJiukong':       [v: string]
  'update:algoTianshang':     [v: string]
  'update:algoMingzhu':       [v: string]
  'update:algoLiunianSihua':  [v: string]
  'update:algoChangsheng':    [v: string]
  'update:sihuaJia':  [v: number]
  'update:sihuaWu':   [v: number]
  'update:sihuaGeng': [v: number]
  'update:sihuaXin':  [v: number]
  'update:sihuaRen':  [v: number]
  'update:sihuaGui':  [v: number]
  'reset':            []
  'apply-preset':     [preset: string]
}>()
</script>

<template>
  <!-- 算法设置折叠区 -->
  <div class="algo-toggle-row">
    <button type="button" class="btn-algo-toggle" @click="emit('update:showAlgoSettings', !showAlgoSettings)">
      ⚙ 安星设置 {{ showAlgoSettings ? '▴' : '▾' }}
    </button>
    <span v-if="hasCustomAlgoSettings" class="algo-custom-badge">已自定义</span>
    <button v-if="showAlgoSettings" type="button" class="btn-sec btn-tiny" @click="emit('reset')">恢复默认</button>
  </div>

  <div v-show="showAlgoSettings" class="algo-panel">
    <!-- 预设方案 -->
    <div class="algo-presets">
      <span class="preset-label">快速预设：</span>
      <button type="button" class="preset-btn" @click="emit('apply-preset','sanhe')"    title="三合派（传统默认）">三合派</button>
      <button type="button" class="preset-btn" @click="emit('apply-preset','feixing')"  title="飞星派设置">飞星派</button>
      <button type="button" class="preset-btn" @click="emit('apply-preset','qintian')"  title="钦天门设置">钦天门</button>
      <button type="button" class="preset-btn" @click="emit('apply-preset','zhongzhou')" title="中州派设置">中州派</button>
    </div>
    <div class="algo-divider"></div>

    <!-- 晚子时 -->
    <div class="algo-group">
      <span class="algo-label">晚子时(23:00~00:00)</span>
      <label class="radio-opt"><input type="radio" :value="true"  :checked="algoLateZishi"  @change="emit('update:algoLateZishi', true)"  />视为次日（默认）</label>
      <label class="radio-opt"><input type="radio" :value="false" :checked="!algoLateZishi" @change="emit('update:algoLateZishi', false)" />视为当日</label>
    </div>
    <!-- 闰月处理 -->
    <div class="algo-group">
      <span class="algo-label">闰月本命盘</span>
      <label class="radio-opt"><input type="radio" value="mid"  :checked="algoLeapMethod==='mid'"  @change="emit('update:algoLeapMethod','mid')"  />月中分界（默认）</label>
      <label class="radio-opt"><input type="radio" value="next" :checked="algoLeapMethod==='next'" @change="emit('update:algoLeapMethod','next')" />视为下月</label>
      <label class="radio-opt"><input type="radio" value="same" :checked="algoLeapMethod==='same'" @change="emit('update:algoLeapMethod','same')" />视为本月</label>
    </div>
    <!-- 安魁钺 -->
    <div class="algo-group">
      <span class="algo-label">安天魁天钺</span>
      <label class="radio-opt"><input type="radio" value="standard"      :checked="algoKuiyue==='standard'"      @change="emit('update:algoKuiyue','standard')"      />六辛逢虎马（默认）</label>
      <label class="radio-opt"><input type="radio" value="gengxin_mahu"  :checked="algoKuiyue==='gengxin_mahu'"  @change="emit('update:algoKuiyue','gengxin_mahu')"  />庚辛逢马虎</label>
      <label class="radio-opt"><input type="radio" value="gengxin_huima" :checked="algoKuiyue==='gengxin_huima'" @change="emit('update:algoKuiyue','gengxin_huima')" />庚辛逢虎马</label>
      <label class="radio-opt"><input type="radio" value="liuxin_mahu"   :checked="algoKuiyue==='liuxin_mahu'"   @change="emit('update:algoKuiyue','liuxin_mahu')"   />六辛逢马虎</label>
    </div>
    <!-- 四化表 -->
    <div class="algo-group sihua-group">
      <span class="algo-label">四化表选项</span>
      <div class="sihua-rows">
        <div class="sihua-row">
          <span class="sihua-stem">甲</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaJia===0" @change="emit('update:sihuaJia',0)" />廉破武阳（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaJia===1" @change="emit('update:sihuaJia',1)" />廉破曲阳</label>
        </div>
        <div class="sihua-row">
          <span class="sihua-stem">戊</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaWu===0" @change="emit('update:sihuaWu',0)" />贪阴右机（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaWu===1" @change="emit('update:sihuaWu',1)" />贪阴阳机</label>
        </div>
        <div class="sihua-row">
          <span class="sihua-stem">庚</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaGeng===0" @change="emit('update:sihuaGeng',0)" />阳武阴同（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaGeng===1" @change="emit('update:sihuaGeng',1)" />阳武同阴</label>
          <label class="radio-opt"><input type="radio" :value="2" :checked="sihuaGeng===2" @change="emit('update:sihuaGeng',2)" />阳武府同</label>
          <label class="radio-opt"><input type="radio" :value="3" :checked="sihuaGeng===3" @change="emit('update:sihuaGeng',3)" />阳武府相</label>
          <label class="radio-opt"><input type="radio" :value="4" :checked="sihuaGeng===4" @change="emit('update:sihuaGeng',4)" />阳武同相</label>
        </div>
        <div class="sihua-row">
          <span class="sihua-stem">辛</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaXin===0" @change="emit('update:sihuaXin',0)" />巨阳曲昌（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaXin===1" @change="emit('update:sihuaXin',1)" />巨阳武昌</label>
        </div>
        <div class="sihua-row">
          <span class="sihua-stem">壬</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaRen===0" @change="emit('update:sihuaRen',0)" />梁紫辅武（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaRen===1" @change="emit('update:sihuaRen',1)" />梁紫府武</label>
          <label class="radio-opt"><input type="radio" :value="2" :checked="sihuaRen===2" @change="emit('update:sihuaRen',2)" />梁紫相武</label>
        </div>
        <div class="sihua-row">
          <span class="sihua-stem">癸</span>
          <label class="radio-opt"><input type="radio" :value="0" :checked="sihuaGui===0" @change="emit('update:sihuaGui',0)" />破巨阴贪（默认）</label>
          <label class="radio-opt"><input type="radio" :value="1" :checked="sihuaGui===1" @change="emit('update:sihuaGui',1)" />破巨阳贪</label>
        </div>
      </div>
    </div>
    <!-- 安天马 -->
    <div class="algo-group">
      <span class="algo-label">安天马</span>
      <label class="radio-opt"><input type="radio" value="year"  :checked="algoTianma==='year'"  @change="emit('update:algoTianma','year')"  />依据年支（默认）</label>
      <label class="radio-opt"><input type="radio" value="month" :checked="algoTianma==='month'" @change="emit('update:algoTianma','month')" />依据月支</label>
    </div>
    <!-- 安天空 -->
    <div class="algo-group">
      <span class="algo-label">安天空</span>
      <label class="radio-opt"><input type="radio" value="standard" :checked="algoTiankong==='standard'" @change="emit('update:algoTiankong','standard')" />常规排法（默认）</label>
      <label class="radio-opt"><input type="radio" value="shun"     :checked="algoTiankong==='shun'"     @change="emit('update:algoTiankong','shun')"     />顺加生时</label>
    </div>
    <!-- 星曜亮度 -->
    <div class="algo-group">
      <span class="algo-label">星曜亮度</span>
      <label class="radio-opt"><input type="radio" value="standard"  :checked="algoBrightness==='standard'"  @change="emit('update:algoBrightness','standard')"  />依据斗数全书（默认）</label>
      <label class="radio-opt"><input type="radio" value="zhongzhou" :checked="algoBrightness==='zhongzhou'" @change="emit('update:algoBrightness','zhongzhou')" />依据中州派理论</label>
      <label class="radio-opt"><input type="radio" value="mod1"      :checked="algoBrightness==='mod1'"      @change="emit('update:algoBrightness','mod1')"      />现代修订亮度一</label>
      <label class="radio-opt"><input type="radio" value="mod2"      :checked="algoBrightness==='mod2'"      @change="emit('update:algoBrightness','mod2')"      />现代修订亮度二</label>
    </div>
    <!-- 安截空旬空 -->
    <div class="algo-group">
      <span class="algo-label">安截空旬空</span>
      <label class="radio-opt"><input type="radio" value="dual"    :checked="algoJiukong==='dual'"    @change="emit('update:algoJiukong','dual')"    />正副双星法（默认）</label>
      <label class="radio-opt"><input type="radio" value="single"  :checked="algoJiukong==='single'"  @change="emit('update:algoJiukong','single')"  />常规单星法</label>
      <label class="radio-opt"><input type="radio" value="zhanyan" :checked="algoJiukong==='zhanyan'" @change="emit('update:algoJiukong','zhanyan')" />占验派排法</label>
    </div>
    <!-- 安天使天伤 -->
    <div class="algo-group">
      <span class="algo-label">安天使天伤</span>
      <label class="radio-opt"><input type="radio" value="standard"  :checked="algoTianshang==='standard'"  @change="emit('update:algoTianshang','standard')"  />常规排法（默认）</label>
      <label class="radio-opt"><input type="radio" value="zhongzhou" :checked="algoTianshang==='zhongzhou'" @change="emit('update:algoTianshang','zhongzhou')" />中州派排法</label>
    </div>
    <!-- 安命主 -->
    <div class="algo-group">
      <span class="algo-label">安命主</span>
      <label class="radio-opt"><input type="radio" value="quanshu"   :checked="algoMingzhu==='quanshu'"   @change="emit('update:algoMingzhu','quanshu')"   />依据斗数全书（默认）</label>
      <label class="radio-opt"><input type="radio" value="zhongzhou" :checked="algoMingzhu==='zhongzhou'" @change="emit('update:algoMingzhu','zhongzhou')" />依据中州派理论</label>
    </div>
    <!-- 流年四化 -->
    <div class="algo-group">
      <span class="algo-label">流年四化</span>
      <label class="radio-opt"><input type="radio" value="year_stem"        :checked="algoLiunianSihua==='year_stem'"        @change="emit('update:algoLiunianSihua','year_stem')"        />依据流年天干</label>
      <label class="radio-opt"><input type="radio" value="life_palace_stem" :checked="algoLiunianSihua==='life_palace_stem'" @change="emit('update:algoLiunianSihua','life_palace_stem')" />依据流年命宫天干（默认）</label>
    </div>
    <!-- 安长生十二神 -->
    <div class="algo-group">
      <span class="algo-label">安长生十二神</span>
      <label class="radio-opt"><input type="radio" value="standard"    :checked="algoChangsheng==='standard'"    @change="emit('update:algoChangsheng','standard')"    />区分阴阳顺逆（默认）</label>
      <label class="radio-opt"><input type="radio" value="water_earth" :checked="algoChangsheng==='water_earth'" @change="emit('update:algoChangsheng','water_earth')" />水土共长生</label>
      <label class="radio-opt"><input type="radio" value="fire_earth"  :checked="algoChangsheng==='fire_earth'"  @change="emit('update:algoChangsheng','fire_earth')"  />火土共长生</label>
    </div>
  </div>
</template>

<style scoped>
.algo-toggle-row { display: flex; align-items: center; gap: var(--sp-3); margin: var(--sp-3) 0 var(--sp-2); flex-wrap: wrap; }
.btn-algo-toggle { background: none; border: 1px solid var(--border-md); border-radius: var(--radius-sm); padding: 5px 12px; font-size: var(--fs-sm); color: var(--text-2); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-algo-toggle:hover { border-color: var(--accent); color: var(--accent); }
.btn-sec { padding: 9px 18px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-sec:hover { border-color: var(--accent); color: var(--accent); }
.btn-tiny { padding: 4px 10px !important; font-size: var(--fs-xs) !important; }
.algo-custom-badge { background: var(--warning, #f59e0b); color: #fff; border-radius: 4px; padding: 2px 8px; font-size: var(--fs-xs); font-weight: 600; }
.algo-panel { background: var(--surface-alt, #f9f9fb); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--sp-3) var(--sp-4); margin-bottom: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3); }
.algo-presets { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.preset-label { font-size: var(--fs-sm); color: var(--text-3); font-weight: 500; }
.preset-btn { padding: 4px 12px; font-size: var(--fs-sm); font-weight: 600; font-family: var(--font-cn); background: linear-gradient(135deg, #fff 0%, #f5f5f4 100%); border: 1px solid var(--border-md); border-radius: 6px; color: var(--text-2); cursor: pointer; transition: all 0.2s ease; }
.preset-btn:hover { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-color: var(--accent); color: var(--accent-dark); }
.algo-divider { height: 1px; background: var(--border); margin: 4px 0; }
.algo-group { display: flex; align-items: flex-start; gap: var(--sp-3); flex-wrap: wrap; }
.algo-label { min-width: 110px; font-size: var(--fs-sm); color: var(--text-3); font-weight: 500; padding-top: 2px; }
.sihua-group { flex-direction: column; gap: var(--sp-2); }
.sihua-group .algo-label { align-self: flex-start; }
.sihua-rows { display: flex; flex-direction: column; gap: var(--sp-2); }
.sihua-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.sihua-stem { min-width: 22px; font-weight: 700; color: var(--accent); font-size: var(--fs-sm); }
.radio-opt { display: flex; align-items: center; gap: 4px; font-size: var(--fs-sm); cursor: pointer; }
</style>
