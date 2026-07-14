import { computed, type Ref } from 'vue'
import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import { useProfileStore } from '@/stores/profile'
import {
  buildBaziStructuralLines,
  buildClassicPendingLines,
  buildClassicCitationRows,
  buildDualTrackReferenceRows,
  buildDualTrackRows,
  buildIztroDisplay,
  buildLiuriSummary,
  buildPalaceStructuredRows,
  buildPillarDetailRows,
  buildProvenanceRows,
  buildValidationLines,
  buildStrengthFactorLines,
  buildYongshenDualTrackRows,
  buildZiweiStructuralLines,
  collectMissingFields,
  formatRelationLines,
  readProvenance,
} from '@/utils/buildEngineTrustDisplay'
import classicsSpotcheck from '@/assets/classics-spotcheck.json'

export function useEngineTrustDisplay(
  bazi: Ref<BaziResponse | null | undefined>,
  ziwei?: Ref<ZiweiResponse | null | undefined>,
) {
  const profile = useProfileStore()
  const missingFields = computed(() => collectMissingFields(bazi.value, ziwei?.value).merged)
  const provenanceRows = computed(() => buildProvenanceRows(
    readProvenance(bazi.value),
    readProvenance(ziwei?.value),
  ))
  const dualTracks = computed(() => [
    ...buildDualTrackRows(bazi.value),
    ...buildYongshenDualTrackRows(bazi.value),
  ])
  const validationLines = computed(() => buildValidationLines(bazi.value))
  const iztro = computed(() => buildIztroDisplay(ziwei?.value, {
    yearDivide: profile.yearDivide,
    dayDivide: profile.dayDivide,
  }))
  const liuri = computed(() => buildLiuriSummary(bazi.value?.liuri_liushi))
  const pillarDetails = computed(() => buildPillarDetailRows(bazi.value))
  const relations = computed(() => formatRelationLines(bazi.value))
  const strengthFactorLines = computed(() => buildStrengthFactorLines(bazi.value))
  const baziStructural = computed(() => buildBaziStructuralLines(bazi.value))
  const ziweiStructural = computed(() => buildZiweiStructuralLines(ziwei?.value))
  const palaceStructured = computed(() => buildPalaceStructuredRows(ziwei?.value))
  const dualTrackReference = computed(() => buildDualTrackReferenceRows())
  const classicPendingLines = computed(() => buildClassicPendingLines(classicsSpotcheck as Array<Record<string, unknown>>))
  const classicCitationRows = computed(() => buildClassicCitationRows(classicsSpotcheck as Array<Record<string, unknown>>))

  return {
    missingFields,
    provenanceRows,
    dualTracks,
    dualTrackReference,
    classicPendingLines,
    classicCitationRows,
    validationLines,
    iztro,
    liuri,
    pillarDetails,
    relations,
    strengthFactorLines,
    baziStructural,
    ziweiStructural,
    palaceStructured,
  }
}
