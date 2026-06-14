<script setup lang="ts">
import type { DayunItem, PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import type { ZiweiChartNote, ZiweiNoteTarget } from '@/composables/useZiweiInteractionState'
import type { ZiweiCompareTarget, ZiweiDayFortune } from '@/composables/useZiweiToolPanels'
import ZiweiCenterOverlayPanels from './ZiweiCenterOverlayPanels.vue'
import ZiweiCenterSummary from './ZiweiCenterSummary.vue'
import ZiweiNotesPanel from './ZiweiNotesPanel.vue'
import ZiweiPalaceCell from './ZiweiPalaceCell.vue'
import ZiweiSihuaLinesOverlay from './ZiweiSihuaLinesOverlay.vue'

type PalaceGridCell = {
  empty: boolean
  pos: number
  palace?: PalaceResponse
}

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

type NotesPanelBindings = {
  visible: boolean
  notes: ZiweiChartNote[]
  editingNote: ZiweiChartNote | null
  noteInput: string
  noteTarget: ZiweiNoteTarget
  noteTargetName: string
  onClose: () => void
  'onUpdate:noteInput': (value: string) => void
  'onUpdate:noteTarget': (value: ZiweiNoteTarget) => void
  'onUpdate:noteTargetName': (value: string) => void
  onAddNote: () => void
  onUpdateNote: () => void
  onCancelEdit: () => void
  onStartEdit: (note: ZiweiChartNote) => void
  onDeleteNote: (id: string) => void
}

type CompareForm = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
}

type CenterOverlayPanelBindings = {
  showSharePanel: boolean
  shareLink: string
  showCalendarView: boolean
  calendarViewYear: number
  calendarViewMonth: number
  calendarGrid: Array<ZiweiDayFortune | null>
  getDayFortuneClass: (score: number) => string
  showComparePanel: boolean
  compareForm: CompareForm
  compareTarget: ZiweiCompareTarget | null
  showBookmarksPanel: boolean
  bookmarkedPalaces: PalaceResponse[]
  onCloseSharePanel: () => void
  onCopyShareLink: () => void
  onPrevCalendarMonth: () => void
  onNextCalendarMonth: () => void
  onCloseCalendarView: () => void
  onCloseComparePanel: () => void
  'onUpdate:compareForm': (value: CompareForm) => void
  onClearCompareTarget: () => void
  onSetCompareTarget: () => void
  onCloseBookmarksPanel: () => void
  onSelectBookmarkedPalace: (index: number) => void
  onTogglePalaceBookmark: (index: number) => void
}

type SihuaColorConfig = {
  color: string
  label: string
}

type SihuaLineItem = {
  fromBranchIdx: number
  toBranchIdx: number
  starName: string
  transform: string
  color: string
  label: string
  isSelfHua: boolean
}

const props = defineProps<{
  result: ZiweiResponse
  currentYear: number
  juColors: Record<number, string>
  notesPanelBindings: NotesPanelBindings
  centerOverlayPanelBindings: CenterOverlayPanelBindings
  palaceGrid: PalaceGridCell[]
  selectedPalace: PalaceResponse | null
  sanfangIndices: Set<number>
  liunianLifePalaceIdx: number
  liuyueLifePalaceIdx: number
  xiaoxianLifePalaceIdx: number
  isPalaceBookmarked: (index: number) => boolean
  palaceDayunMap: Record<number, DayunItem>
  palaceLiunianInfo: Record<number, PalaceLiunianInfo>
  palaceDaxianNames: Record<number, string>
  palaceLiunianNames: Record<number, string>
  palaceLiuyueNames: Record<number, string>
  palaceXiaoxianNames: Record<number, string>
  starDisplayOpts: StarDisplayOptions
  overlayOpts: OverlayDisplayOptions
  daxianSihuaMap: Record<string, string>
  liunianSihuaMap: Record<string, string>
  liuyueSihuaMap: Record<string, string>
  xiaoxianSihuaMap: Record<string, string>
  tfColorStyle: (transform: string) => Record<string, string>
  tfOutlineStyle: (transform: string) => Record<string, string>
  selectPalace: (palace: PalaceResponse) => void
  togglePalaceBookmark: (palaceIndex: number) => void
  shiftDay: (delta: number) => void
  shiftHour: (delta: number) => void
  returnChart: () => void
  showSihuaLines: boolean
  chartMode: string
  sihuaLines: SihuaLineItem[]
  sihuaColors: Record<string, SihuaColorConfig>
  getPalaceCenter: (branchIdx: number) => { x: number; y: number }
  getCurvedPath: (fromIdx: number, toIdx: number, curveOffset?: number) => string
  getCurvedMidpoint: (fromIdx: number, toIdx: number, curveOffset?: number) => { x: number; y: number }
}>()
</script>

<template>
  <div class="palace-grid-wrap">
    <div class="grid-compass">
      <div class="compass-cell compass-nw"></div>
      <div class="compass-cell compass-n">南</div>
      <div class="compass-cell compass-ne"></div>
    </div>

    <div class="grid-body">
      <div class="compass-side compass-w">东</div>
      <div class="palace-grid-pro">
        <template v-for="cell in props.palaceGrid" :key="cell.pos">
          <div v-if="cell.empty" class="pc-center">
            <div class="pc-center-inner">
              <ZiweiCenterSummary
                :result="props.result"
                :current-year="props.currentYear"
                :ju-colors="props.juColors"
                @shift-day="props.shiftDay"
                @shift-hour="props.shiftHour"
                @return-chart="props.returnChart"
              />

              <ZiweiNotesPanel v-bind="props.notesPanelBindings" />
              <ZiweiCenterOverlayPanels v-bind="props.centerOverlayPanelBindings" />
            </div>
          </div>

          <ZiweiPalaceCell
            v-else-if="cell.palace"
            :palace="cell.palace"
            :is-selected="props.selectedPalace?.index === cell.palace.index"
            :is-sanfang="props.sanfangIndices.has(cell.palace.index)"
            :is-liunian-life="props.overlayOpts.showLiunian && props.liunianLifePalaceIdx === cell.palace.index"
            :is-liuyue-life="props.overlayOpts.showLiuyue && props.liuyueLifePalaceIdx === cell.palace.index"
            :is-xiaoxian-life="props.overlayOpts.showXiaoxian && props.xiaoxianLifePalaceIdx === cell.palace.index"
            :is-laiyin="cell.palace.name === props.result.laiyin_palace"
            :is-bookmarked="props.isPalaceBookmarked(cell.palace.index)"
            :overlap-tag="props.overlayOpts.showLiunian && props.liunianLifePalaceIdx === cell.palace.index
              ? (props.overlayOpts.showDaxian && props.palaceDaxianNames[cell.palace.index] === '大命' ? '叠限'
                : cell.palace.index === 0 ? '叠命'
                : cell.palace.name === props.result.laiyin_palace ? '叠来因'
                : '')
              : ''"
            :palace-dayun="props.palaceDayunMap[cell.palace.index]"
            :palace-liunian-info="props.palaceLiunianInfo[cell.palace.index]"
            :daxian-name="props.palaceDaxianNames[cell.palace.index]"
            :liunian-name="props.palaceLiunianNames[cell.palace.index]"
            :liuyue-name="props.palaceLiuyueNames[cell.palace.index]"
            :xiaoxian-name="props.palaceXiaoxianNames[cell.palace.index]"
            :star-display-opts="props.starDisplayOpts"
            :overlay-opts="props.overlayOpts"
            :daxian-sihua-map="props.daxianSihuaMap"
            :liunian-sihua-map="props.liunianSihuaMap"
            :liuyue-sihua-map="props.liuyueSihuaMap"
            :xiaoxian-sihua-map="props.xiaoxianSihuaMap"
            :tf-color-style="props.tfColorStyle"
            :tf-outline-style="props.tfOutlineStyle"
            @select="props.selectPalace"
            @toggle-bookmark="props.togglePalaceBookmark"
          />
        </template>
      </div>
      <div class="compass-side compass-e">西</div>

      <ZiweiSihuaLinesOverlay
        :visible="props.showSihuaLines"
        :chart-mode="props.chartMode"
        :lines="props.sihuaLines"
        :colors="props.sihuaColors"
        :get-palace-center="props.getPalaceCenter"
        :get-curved-path="props.getCurvedPath"
        :get-curved-midpoint="props.getCurvedMidpoint"
      />
    </div>

    <div class="grid-compass">
      <div class="compass-cell compass-sw"></div>
      <div class="compass-cell compass-s">北</div>
      <div class="compass-cell compass-se"></div>
    </div>
  </div>
</template>

<style scoped>
.palace-grid-wrap {
  margin-bottom: var(--sp-5);
  user-select: none;
  overflow-y: auto;
  max-height: 70vh;
}

.grid-compass {
  display: grid;
  grid-template-columns: 26px 1fr 26px;
  align-items: center;
}

.compass-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.compass-n,
.compass-s {
  text-align: center;
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: 1px;
  padding: 3px 0;
}

.grid-body {
  display: flex;
  align-items: stretch;
  position: relative;
}

.compass-side {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: 1px;
  writing-mode: vertical-rl;
  flex-shrink: 0;
}

.palace-grid-pro {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border: 1.5px solid #c9b99a;
  border-radius: 2px;
  overflow: hidden;
  flex: 1;
  background: #e8dcc8;
}

.pc-center {
  grid-column: span 2;
  grid-row: span 2;
  background: linear-gradient(135deg, #fffff5 0%, #fdf6e3 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
}

.pc-center-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  text-align: center;
  width: 100%;
}
</style>
