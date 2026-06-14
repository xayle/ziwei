import { computed, type ComputedRef, type Ref } from 'vue'
import type { DayunItem, PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import type { ZiweiChartNote, ZiweiNoteTarget } from '@/composables/useZiweiInteractionState'
import type { ZiweiCompareTarget, ZiweiDayFortune } from '@/composables/useZiweiToolPanels'

type MaybeRef<T> = Ref<T> | ComputedRef<T>

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

export type ZiweiChartCanvasBindings = {
  result: ZiweiResponse
  currentYear: number
  juColors: Record<number, string>
  notesPanelBindings: {
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
}

type UseZiweiChartCanvasBindingsOptions = {
  result: Ref<ZiweiResponse | null>
  currentYear: number
  juColors: Record<number, string>
  showNotesPanel: Ref<boolean>
  chartNotes: Ref<ZiweiChartNote[]>
  editingNote: Ref<ZiweiChartNote | null>
  noteInput: Ref<string>
  noteTarget: Ref<ZiweiNoteTarget>
  noteTargetName: Ref<string>
  addNote: () => void
  updateNote: () => void
  startEditNote: (note: ZiweiChartNote) => void
  cancelEditNote: () => void
  deleteNote: (id: string) => void
  centerOverlayPanelBindings: MaybeRef<CenterOverlayPanelBindings>
  palaceGrid: MaybeRef<PalaceGridCell[]>
  selectedPalace: Ref<PalaceResponse | null>
  sanfangIndices: MaybeRef<Set<number>>
  liunianLifePalaceIdx: MaybeRef<number>
  liuyueLifePalaceIdx: MaybeRef<number>
  xiaoxianLifePalaceIdx: MaybeRef<number>
  isPalaceBookmarked: (index: number) => boolean
  palaceDayunMap: MaybeRef<Record<number, DayunItem>>
  palaceLiunianInfo: MaybeRef<Record<number, PalaceLiunianInfo>>
  palaceDaxianNames: MaybeRef<Record<number, string>>
  palaceLiunianNames: MaybeRef<Record<number, string>>
  palaceLiuyueNames: MaybeRef<Record<number, string>>
  palaceXiaoxianNames: MaybeRef<Record<number, string>>
  starDisplayOpts: StarDisplayOptions
  overlayOpts: OverlayDisplayOptions
  daxianSihuaMap: MaybeRef<Record<string, string>>
  liunianSihuaMap: MaybeRef<Record<string, string>>
  liuyueSihuaMap: MaybeRef<Record<string, string>>
  xiaoxianSihuaMap: MaybeRef<Record<string, string>>
  tfColorStyle: (transform: string) => Record<string, string>
  tfOutlineStyle: (transform: string) => Record<string, string>
  selectPalace: (palace: PalaceResponse) => void
  togglePalaceBookmark: (palaceIndex: number) => void
  shiftDay: (delta: number) => void
  shiftHour: (delta: number) => void
  returnChart: () => void
  showSihuaLines: Ref<boolean>
  chartMode: Ref<string>
  sihuaLines: MaybeRef<SihuaLineItem[]>
  sihuaColors: Record<string, SihuaColorConfig>
  getPalaceCenter: (branchIdx: number) => { x: number; y: number }
  getCurvedPath: (fromIdx: number, toIdx: number, curveOffset?: number) => string
  getCurvedMidpoint: (fromIdx: number, toIdx: number, curveOffset?: number) => { x: number; y: number }
}

export function useZiweiChartCanvasBindings(options: UseZiweiChartCanvasBindingsOptions) {
  const notesPanelBindings = computed(() => ({
    visible: options.showNotesPanel.value,
    notes: options.chartNotes.value,
    editingNote: options.editingNote.value,
    noteInput: options.noteInput.value,
    noteTarget: options.noteTarget.value,
    noteTargetName: options.noteTargetName.value,
    onClose: () => {
      options.showNotesPanel.value = false
    },
    'onUpdate:noteInput': (value: string) => {
      options.noteInput.value = value
    },
    'onUpdate:noteTarget': (value: ZiweiNoteTarget) => {
      options.noteTarget.value = value
    },
    'onUpdate:noteTargetName': (value: string) => {
      options.noteTargetName.value = value
    },
    onAddNote: options.addNote,
    onUpdateNote: options.updateNote,
    onCancelEdit: options.cancelEditNote,
    onStartEdit: options.startEditNote,
    onDeleteNote: options.deleteNote,
  }))

  const chartCanvasBindings = computed<ZiweiChartCanvasBindings>(() => ({
    result: options.result.value!,
    currentYear: options.currentYear,
    juColors: options.juColors,
    notesPanelBindings: notesPanelBindings.value,
    centerOverlayPanelBindings: options.centerOverlayPanelBindings.value,
    palaceGrid: options.palaceGrid.value,
    selectedPalace: options.selectedPalace.value,
    sanfangIndices: options.sanfangIndices.value,
    liunianLifePalaceIdx: options.liunianLifePalaceIdx.value,
    liuyueLifePalaceIdx: options.liuyueLifePalaceIdx.value,
    xiaoxianLifePalaceIdx: options.xiaoxianLifePalaceIdx.value,
    isPalaceBookmarked: options.isPalaceBookmarked,
    palaceDayunMap: options.palaceDayunMap.value,
    palaceLiunianInfo: options.palaceLiunianInfo.value,
    palaceDaxianNames: options.palaceDaxianNames.value,
    palaceLiunianNames: options.palaceLiunianNames.value,
    palaceLiuyueNames: options.palaceLiuyueNames.value,
    palaceXiaoxianNames: options.palaceXiaoxianNames.value,
    starDisplayOpts: options.starDisplayOpts,
    overlayOpts: options.overlayOpts,
    daxianSihuaMap: options.daxianSihuaMap.value,
    liunianSihuaMap: options.liunianSihuaMap.value,
    liuyueSihuaMap: options.liuyueSihuaMap.value,
    xiaoxianSihuaMap: options.xiaoxianSihuaMap.value,
    tfColorStyle: options.tfColorStyle,
    tfOutlineStyle: options.tfOutlineStyle,
    selectPalace: options.selectPalace,
    togglePalaceBookmark: options.togglePalaceBookmark,
    shiftDay: options.shiftDay,
    shiftHour: options.shiftHour,
    returnChart: options.returnChart,
    showSihuaLines: options.showSihuaLines.value,
    chartMode: options.chartMode.value,
    sihuaLines: options.sihuaLines.value,
    sihuaColors: options.sihuaColors,
    getPalaceCenter: options.getPalaceCenter,
    getCurvedPath: options.getCurvedPath,
    getCurvedMidpoint: options.getCurvedMidpoint,
  }))

  return {
    chartCanvasBindings,
  }
}
