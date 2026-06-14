<script setup lang="ts">
import { computed } from 'vue'
import type { DayunItem, PalaceResponse } from '@/api/ziwei'

type StarDisplayOptions = {
  showMainStars: boolean
  showAuxStars: boolean
  showTransforms: boolean
  showBrightness: boolean
  showChangsheng: boolean
  showBoshi: boolean
  showJiangSui: boolean
  auxLimit: number
}

type OverlayDisplayOptions = {
  showDaxian: boolean
  showLiunian: boolean
  showLiuyue: boolean
  showXiaoxian: boolean
}

type PalaceLiunianInfo = {
  age: number
  year: number
}

const props = defineProps<{
  palace: PalaceResponse
  isSelected: boolean
  isSanfang: boolean
  isLiunianLife: boolean
  isLiuyueLife: boolean
  isXiaoxianLife: boolean
  isLaiyin: boolean
  isBookmarked: boolean
  overlapTag?: string
  palaceDayun?: DayunItem | null
  palaceLiunianInfo?: PalaceLiunianInfo | null
  daxianName?: string
  liunianName?: string
  liuyueName?: string
  xiaoxianName?: string
  starDisplayOpts: StarDisplayOptions
  overlayOpts: OverlayDisplayOptions
  daxianSihuaMap: Record<string, string>
  liunianSihuaMap: Record<string, string>
  liuyueSihuaMap: Record<string, string>
  xiaoxianSihuaMap: Record<string, string>
  tfColorStyle: (transform: string) => Record<string, string>
  tfOutlineStyle: (transform: string) => Record<string, string>
}>()

const emit = defineEmits<{
  select: [palace: PalaceResponse]
  'toggle-bookmark': [palaceIndex: number]
}>()

const cellClasses = computed(() => [
  'pc-cell',
  props.palace.name.includes('命') ? 'pc-life' : '',
  props.palace.name.includes('身') ? 'pc-body' : '',
  props.isSelected ? 'pc-sel' : '',
  props.isSanfang ? 'pc-sanfang' : '',
  props.isLiunianLife ? 'pc-liunian-life' : '',
  props.isLiuyueLife ? 'pc-liuyue-life' : '',
  props.isXiaoxianLife ? 'pc-xiaoxian-life' : '',
])

const auxStarsText = computed(() => {
  const limit = props.starDisplayOpts.auxLimit || props.palace.aux_stars.length
  return props.palace.aux_stars.slice(0, limit).map(s => s.name).join('·')
})

function handleSelect() {
  emit('select', props.palace)
}

function handleToggleBookmark() {
  emit('toggle-bookmark', props.palace.index)
}
</script>

<template>
  <div :class="cellClasses" :title="palace.tooltip || ''" @click="handleSelect()">
    <div class="pc-head">
      <div class="pc-head-left">
        <span class="pc-pname">{{ palace.name.replace('宫', '') }}</span>
        <span v-if="palace.name.includes('命')" class="pc-life-tag">命</span>
        <span v-if="palace.name.includes('身')" class="pc-body-tag">身</span>
        <span v-if="isLaiyin" class="pc-laiyin-tag">来因</span>
        <span v-if="overlapTag" :class="['pc-overlap-tag', overlapTag === '叠来因' ? 'pc-laiyin-tag' : '']" >{{ overlapTag }}</span>
        <button
          class="pc-bookmark-btn"
          :class="{ bookmarked: isBookmarked }"
          :title="isBookmarked ? '取消收藏' : '收藏此宫'"
          @click.stop="handleToggleBookmark()"
        >
          {{ isBookmarked ? '★' : '☆' }}
        </button>
        <span v-if="overlayOpts.showDaxian && daxianName" class="pc-daxian-name">{{ daxianName }}</span>
        <span v-if="overlayOpts.showLiunian && liunianName" class="pc-liunian-name">{{ liunianName }}</span>
        <span v-if="overlayOpts.showLiuyue && liuyueName" class="pc-liuyue-name">{{ liuyueName }}</span>
        <span v-if="overlayOpts.showXiaoxian && xiaoxianName" class="pc-xiaoxian-name">{{ xiaoxianName }}</span>
      </div>
      <span class="pc-gzhi">{{ palace.stem }}{{ palace.branch }}</span>
    </div>

    <div class="pc-da-row">
      <span v-if="palaceDayun" class="pc-da">{{ palaceDayun.start_age }}-{{ palaceDayun.end_age }}岁</span>
      <span v-if="palaceLiunianInfo" class="pc-liunian-age">{{ palaceLiunianInfo.age }}岁</span>
      <span v-if="palace.changsheng && starDisplayOpts.showChangsheng" class="pc-cs">{{ palace.changsheng }}</span>
      <span v-if="palace.jiangqian_star && starDisplayOpts.showJiangSui" class="pc-jiangqian">将{{ palace.jiangqian_star }}</span>
      <span v-if="palace.suiqian_star && starDisplayOpts.showJiangSui" class="pc-suiqian">岁{{ palace.suiqian_star }}</span>
    </div>

    <div v-if="starDisplayOpts.showBoshi && palace.dayun_boshi?.length" class="pc-boshi-row">
      <span v-for="boshi in palace.dayun_boshi" :key="boshi" class="pc-boshi">{{ boshi }}</span>
    </div>

    <div v-if="starDisplayOpts.showMainStars" class="pc-mstars">
      <div v-for="star in palace.main_stars" :key="star.name" class="pc-mstar">
        <span :class="['pc-sn', `pc-br${star.brightness_val}`]">{{ star.name }}</span>
        <template v-if="starDisplayOpts.showBrightness">
          <span class="pc-sbr-sep">·</span>
          <span class="pc-sbr">{{ star.brightness }}</span>
        </template>
        <template v-if="starDisplayOpts.showTransforms">
          <span
            v-for="transform in star.transforms"
            :key="transform"
            class="pc-tf"
            :style="tfColorStyle(transform)"
          >
            {{ transform.startsWith('化') ? '生' + transform.slice(1) : transform[0] + transform.slice(2) }}
          </span>
        </template>
        <span
          v-if="overlayOpts.showDaxian && daxianSihuaMap[star.name]"
          class="pc-tf pc-tf-daxian"
          :style="tfOutlineStyle(daxianSihuaMap[star.name])"
        >
          限{{ daxianSihuaMap[star.name].slice(1) }}
        </span>
        <span
          v-if="overlayOpts.showLiunian && liunianSihuaMap[star.name]"
          class="pc-tf pc-tf-liunian"
          :style="tfOutlineStyle(liunianSihuaMap[star.name])"
        >
          年{{ liunianSihuaMap[star.name].slice(1) }}
        </span>
        <span
          v-if="overlayOpts.showLiuyue && liuyueSihuaMap[star.name]"
          class="pc-tf pc-tf-liuyue"
          :style="tfOutlineStyle(liuyueSihuaMap[star.name])"
        >
          月{{ liuyueSihuaMap[star.name].slice(1) }}
        </span>
        <span
          v-if="overlayOpts.showXiaoxian && xiaoxianSihuaMap[star.name]"
          class="pc-tf pc-tf-xiaoxian"
          :style="tfOutlineStyle(xiaoxianSihuaMap[star.name])"
        >
          小{{ xiaoxianSihuaMap[star.name].slice(1) }}
        </span>
      </div>
    </div>

    <div v-if="starDisplayOpts.showAuxStars && palace.aux_stars.length" class="pc-aux">
      <template
        v-for="(aux, auxIdx) in palace.aux_stars.slice(0, starDisplayOpts.auxLimit || palace.aux_stars.length)"
        :key="aux.name"
      >
        <span v-if="auxIdx > 0" class="pc-aux-sep">·</span>
        <span :class="['pc-aux-n', `pc-br${aux.brightness_val}`]">{{ aux.name }}</span>
        <span
          v-if="starDisplayOpts.showBrightness && aux.brightness !== '平'"
          class="pc-sbr"
        >{{ aux.brightness }}</span>
        <span
          v-if="overlayOpts.showDaxian && daxianSihuaMap[aux.name]"
          class="pc-tf pc-tf-daxian"
          :style="tfOutlineStyle(daxianSihuaMap[aux.name])"
        >限{{ daxianSihuaMap[aux.name].slice(1) }}</span>
        <span
          v-if="overlayOpts.showLiunian && liunianSihuaMap[aux.name]"
          class="pc-tf pc-tf-liunian"
          :style="tfOutlineStyle(liunianSihuaMap[aux.name])"
        >年{{ liunianSihuaMap[aux.name].slice(1) }}</span>
        <span
          v-if="overlayOpts.showLiuyue && liuyueSihuaMap[aux.name]"
          class="pc-tf pc-tf-liuyue"
          :style="tfOutlineStyle(liuyueSihuaMap[aux.name])"
        >月{{ liuyueSihuaMap[aux.name].slice(1) }}</span>
        <span
          v-if="overlayOpts.showXiaoxian && xiaoxianSihuaMap[aux.name]"
          class="pc-tf pc-tf-xiaoxian"
          :style="tfOutlineStyle(xiaoxianSihuaMap[aux.name])"
        >小{{ xiaoxianSihuaMap[aux.name].slice(1) }}</span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.pc-cell {
  background: #fffdf7;
  padding: 5px 5px 4px;
  cursor: pointer;
  min-height: 108px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  transition: background var(--dur-fast);
  position: relative;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
}

.pc-cell:last-child {
  border-right: none;
}

.pc-cell:hover {
  background: #fef9ee;
}

.pc-sel {
  background: #fef3d8 !important;
  box-shadow: inset 0 0 0 2px #c07a00;
}

.pc-sanfang {
  background: rgba(254, 243, 216, 0.4);
  box-shadow: inset 0 0 0 1px rgba(192, 122, 0, 0.3);
}

.pc-life {
  border-top: 3px solid #dc2626 !important;
}

.pc-body {
  border-top: 3px solid #2563eb !important;
}

.pc-liunian-life {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%) !important;
  box-shadow: inset 0 0 0 2px #7c3aed;
}

.pc-liuyue-life {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%) !important;
  box-shadow: inset 0 0 0 2px #ea580c;
}

.pc-xiaoxian-life {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
  box-shadow: inset 0 0 0 2px #059669;
}

.pc-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2px;
}

.pc-head-left {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.pc-pname {
  font-size: 10px;
  color: #78716c;
  font-weight: 600;
  font-family: var(--font-cn);
  letter-spacing: 0.5px;
}

.pc-life-tag,
.pc-body-tag,
.pc-laiyin-tag {
  font-size: 8px;
  padding: 0 2px;
  color: #fff;
  border-radius: 2px;
  font-weight: 700;
  line-height: 1.4;
}

.pc-life-tag {
  background: #dc2626;
}

.pc-body-tag {
  background: #2563eb;
}

.pc-laiyin-tag {
  background: #b45309;
}

.pc-overlap-tag {
  background: #0f766e;
}
.pc-overlap-tag.pc-laiyin-tag {
  background: #b45309;
}

.pc-gzhi {
  font-size: 12px;
  color: #44403c;
  font-weight: 700;
  font-family: var(--font-cn);
  white-space: nowrap;
  flex-shrink: 0;
}

.pc-da-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.pc-da {
  font-size: 9px;
  color: #b45309;
  font-weight: 700;
  background: rgba(180, 83, 9, 0.08);
  border-radius: 2px;
  padding: 0 3px;
}

.pc-liunian-age {
  font-size: 8px;
  color: #7c3aed;
  font-weight: 600;
  background: rgba(124, 58, 237, 0.1);
  border-radius: 2px;
  padding: 0 2px;
}

.pc-daxian-name,
.pc-liunian-name,
.pc-liuyue-name,
.pc-xiaoxian-name {
  font-size: 7px;
  font-weight: 700;
  border-radius: 2px;
  padding: 0 2px;
  margin-left: 2px;
}

.pc-daxian-name {
  color: #0d9488;
  background: rgba(13, 148, 136, 0.12);
}

.pc-liunian-name {
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.1);
}

.pc-liuyue-name {
  color: #ea580c;
  background: rgba(234, 88, 12, 0.1);
}

.pc-xiaoxian-name {
  color: #059669;
  background: rgba(5, 150, 105, 0.1);
}

.pc-cs {
  font-size: 8px;
  color: #a8a29e;
  margin-left: auto;
}

.pc-jiangqian,
.pc-suiqian {
  font-size: 7px;
  margin-left: 2px;
}

.pc-jiangqian {
  color: #10b981;
}

.pc-suiqian {
  color: #f59e0b;
}

.pc-boshi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 1px;
}

.pc-boshi {
  font-size: 7px;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 2px;
  padding: 0 2px;
}

.pc-mstars {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  margin-top: 2px;
}

.pc-mstar {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: nowrap;
}

.pc-sn {
  font-size: 14px;
  font-weight: 900;
  font-family: var(--font-cn);
  line-height: 1.1;
}

.pc-br6 {
  color: #92400e;
}

.pc-br5 {
  color: #dc2626;
}

.pc-br4 {
  color: #b45309;
}

.pc-br3 {
  color: #1d4ed8;
}

.pc-br2 {
  color: #374151;
}

.pc-br1 {
  color: #78716c;
}

.pc-br0 {
  color: #a8a29e;
}

.pc-sbr {
  font-size: 8px;
  color: #a8a29e;
  line-height: 1;
  margin-top: 1px;
}

.pc-sbr-sep {
  font-size: 8px;
  color: #d1ccc4;
  line-height: 1;
  margin-top: 1px;
  user-select: none;
}

.pc-tf {
  font-size: 9px;
  font-weight: 800;
  padding: 0 3px;
  border-radius: 2px;
  line-height: 1.5;
  color: #fff;
  flex-shrink: 0;
}

.pc-tf-daxian {
  font-size: 8px;
  opacity: 0.9;
  border: 1px dashed currentColor;
  background: transparent !important;
  color: #334155 !important;
}

.pc-tf-liunian {
  font-size: 8px;
  opacity: 0.9;
  border: 1px dotted currentColor;
  background: transparent !important;
  color: #334155 !important;
}

.pc-tf-liuyue {
  font-size: 8px;
  opacity: 0.9;
  border: 1px solid currentColor;
  border-radius: 3px;
  background: transparent !important;
  color: #334155 !important;
}

.pc-tf-xiaoxian {
  font-size: 8px;
  opacity: 0.9;
  border: 1.5px double currentColor;
  border-radius: 3px;
  background: transparent !important;
  color: #334155 !important;
}

.pc-tf-daxian[style*='化禄'],
.pc-tf-liunian[style*='化禄'],
.pc-tf-liuyue[style*='化禄'],
.pc-tf-xiaoxian[style*='化禄'] {
  color: #166534 !important;
}

.pc-tf-daxian[style*='化权'],
.pc-tf-liunian[style*='化权'],
.pc-tf-liuyue[style*='化权'],
.pc-tf-xiaoxian[style*='化权'] {
  color: #991b1b !important;
}

.pc-tf-daxian[style*='化科'],
.pc-tf-liunian[style*='化科'],
.pc-tf-liuyue[style*='化科'],
.pc-tf-xiaoxian[style*='化科'] {
  color: #1e40af !important;
}

.pc-tf-daxian[style*='化忌'],
.pc-tf-liunian[style*='化忌'],
.pc-tf-liuyue[style*='化忌'],
.pc-tf-xiaoxian[style*='化忌'] {
  color: #5b21b6 !important;
}

.pc-aux {
  font-size: 9px;
  color: #a8a29e;
  line-height: 1.6;
  word-break: break-all;
  margin-top: auto;
  padding-top: 2px;
  border-top: 1px dashed #e5e0d8;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1px;
}

.pc-aux-n {
  font-size: 9px;
  color: #a8a29e;
}

.pc-aux-sep {
  font-size: 9px;
  color: #d1ccc4;
  user-select: none;
}

.pc-bookmark-btn {
  padding: 0 2px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 11px;
  color: #d1d5db;
  transition: all 0.2s;
  opacity: 0.5;
}

.pc-cell:hover .pc-bookmark-btn {
  opacity: 1;
}

.pc-bookmark-btn:hover {
  color: #fbbf24;
}

.pc-bookmark-btn.bookmarked {
  color: #f59e0b;
  opacity: 1;
}

@media print {
  .pc-cell {
    background: #fff !important;
    border-color: #333;
    min-height: 100px;
    padding: 6px;
  }

  .pc-pname {
    font-size: 11pt;
    font-weight: bold;
    color: #000;
  }

  .pc-gzhi {
    font-size: 9pt;
    color: #333;
  }

  .pc-sn {
    font-size: 10pt;
    font-weight: bold;
    color: #000;
  }

  .pc-sbr {
    font-size: 8pt;
    color: #666;
  }

  .pc-tf {
    font-size: 8pt !important;
    padding: 1px 3px !important;
    border: 1px solid #333;
  }

  .pc-aux {
    font-size: 8pt;
    color: #666;
  }

  .pc-da,
  .pc-cs {
    font-size: 8pt;
    color: #333;
  }
}

@media (max-width: 600px) {
  .pc-cell {
    min-height: 80px;
    padding: 4px 3px;
  }

  .pc-sn {
    font-size: 12px;
  }

  .pc-gzhi {
    font-size: 11px;
  }
}
</style>
