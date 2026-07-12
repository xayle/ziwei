import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProfileStore, type ProfileData } from '@/stores/profile'
import {
  FUSHENG_FLOW_STEPS,
  isFlowStepReady,
  resolveFlowStepId,
  type FlowStepId,
} from '@/utils/fushengFlow'
import {
  getArchiveBlockers,
  getArchiveCompleteness,
  getArchiveBlockerLabel,
  getArchiveEnhancerLabel,
  getArchiveEnhancers,
  isArchiveReady,
} from '@/utils/profileReadiness'
import { getTimeConfidence } from '@/utils/profileMetrics'

export function useFushengFlow() {
  const router = useRouter()
  const route = useRoute()
  const profile = useProfileStore()

  const profileData = computed<ProfileData>(() => profile.asProfileData())

  const isArchiveComplete = computed(() => isArchiveReady(profileData.value))
  const hasBirthDt = computed(() => !!profile.birthDt?.trim())
  const completeness = computed(() => getArchiveCompleteness(profileData.value))
  const archiveBlockers = computed(() => getArchiveBlockers(profileData.value))
  const archiveEnhancers = computed(() => getArchiveEnhancers(profileData.value))
  const timeConfidence = computed(() => getTimeConfidence(profileData.value))
  const currentStepId = computed<FlowStepId>(() => resolveFlowStepId(route.path))

  const flowSteps = computed(() =>
    FUSHENG_FLOW_STEPS.map((step) => ({
      ...step,
      ready: isFlowStepReady(step, isArchiveComplete.value),
      active: step.id === currentStepId.value,
      done: getStepDone(step.id, currentStepId.value),
    })),
  )

  function getStepDone(stepId: FlowStepId, current: FlowStepId): boolean {
    const order = FUSHENG_FLOW_STEPS.map((s) => s.id)
    return order.indexOf(stepId) < order.indexOf(current)
  }

  function navigateToStep(path: string, requiresBirth = false) {
    if (requiresBirth && !isArchiveComplete.value) {
      router.push({ path: '/profile', query: { reason: 'archive', redirect: path } })
      return
    }
    if (route.path !== path) {
      router.push(path)
    }
  }

  return {
    profile,
    profileData,
    isArchiveComplete,
    hasBirthDt,
    completeness,
    archiveBlockers,
    archiveEnhancers,
    timeConfidence,
    currentStepId,
    flowSteps,
    getArchiveBlockerLabel,
    getArchiveEnhancerLabel,
    navigateToStep,
  }
}
