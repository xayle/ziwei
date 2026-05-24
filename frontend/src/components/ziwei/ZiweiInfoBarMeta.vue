<script setup lang="ts">
import type { ZiweiResponse } from '@/api/ziwei'

const props = defineProps<{
  result: ZiweiResponse
  juColors: Record<number | string, string>
}>()
</script>

<template>
  <span class="info-item">
    <b>{{ props.result.birth_solar }}</b> · {{ props.result.gender }}
  </span>
  <span class="info-item">
    农历 {{ props.result.lunar.lunar_year }}年
    {{ props.result.lunar.is_leap_month ? '闰' : '' }}{{ props.result.lunar.lunar_month }}月{{ props.result.lunar.lunar_day }}日
  </span>
  <span class="info-item">
    命宫：<b>{{ props.result.life_palace_gz }}</b>
    &nbsp;身宫：<b>{{ props.result.body_palace_gz }}</b>
    <template v-if="props.result.laiyin_palace">
      &nbsp;来因：<b>{{ props.result.laiyin_palace.replace('宫', '') }}</b>
    </template>
  </span>
  <span class="info-item">
    <span class="ju-badge" :style="{ background: props.juColors[props.result.wuxing_ju] }">
      {{ props.result.wuxing_ju_name }}
    </span>
  </span>
  <span v-if="props.result.life_ruler_star" class="info-item">
    命主：<b>{{ props.result.life_ruler_star }}</b>
  </span>
  <span v-if="props.result.body_ruler_star" class="info-item">
    身主：<b>{{ props.result.body_ruler_star }}</b>
  </span>
  <span v-if="props.result.true_solar_time" class="info-item">
    真太阳时：<b>{{ props.result.true_solar_time }}</b>
  </span>
</template>

<style scoped>
.info-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.info-item b {
  color: var(--text);
}

.ju-badge {
  padding: 2px 10px;
  border-radius: 12px;
  color: #fff;
  font-size: var(--fs-xs);
  font-weight: 700;
}

@media print {
  .info-item {
    font-size: 10pt;
  }
}
</style>
