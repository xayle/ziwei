<script setup lang="ts">
import type { ZiweiResponse } from '@/api/ziwei'

const props = defineProps<{
  result: ZiweiResponse
  currentYear: number
  juColors: Record<number, string>
}>()

const emit = defineEmits<{
  shiftDay: [delta: number]
  shiftHour: [delta: number]
  returnChart: []
}>()

function isCurrentDayun(startYear: number) {
  return startYear <= props.currentYear && (startYear + 10) > props.currentYear
}
</script>

<template>
  <div class="pc-center-top">
    <span class="pc-cj" :style="{ color: props.juColors[props.result.wuxing_ju] }">{{ props.result.wuxing_ju_name }}</span>
    <span class="pc-cg-badge">{{ props.result.gender }}</span>
  </div>

  <div class="pc-sizhu">
    <span class="pc-sz-item" title="年柱">{{ props.result.lunar.year_gz }}</span>
    <span class="pc-sz-item" title="节气月柱">{{ props.result.lunar.jieqi_month_gz || props.result.lunar.month_gz }}</span>
    <span class="pc-sz-item" title="日柱">{{ props.result.lunar.day_gz }}</span>
    <span class="pc-sz-item pc-sz-hour" title="时柱">{{ props.result.lunar.hour_gz || props.result.lunar.hour_branch + '时' }}</span>
  </div>

  <div v-if="props.result.lunar.jieqi_month_gz && props.result.lunar.jieqi_month_gz !== props.result.lunar.month_gz" class="pc-sizhu pc-sizhu-alt">
    <span class="pc-sz-item pc-sz-alt" title="年柱">{{ props.result.lunar.year_gz }}</span>
    <span class="pc-sz-item pc-sz-alt" title="农历月柱">{{ props.result.lunar.month_gz }}</span>
    <span class="pc-sz-item pc-sz-alt" title="日柱">{{ props.result.lunar.day_gz }}</span>
    <span class="pc-sz-item pc-sz-alt pc-sz-hour" title="时柱">{{ props.result.lunar.hour_gz || props.result.lunar.hour_branch + '时' }}</span>
  </div>

  <div class="pc-divider"></div>

  <div class="pc-birth-info">
    <div class="pc-cb">{{ props.result.birth_solar }}</div>
    <div class="pc-cl">农历{{ props.result.lunar.lunar_year }}年{{ props.result.lunar.is_leap_month ? '闰' : '' }}{{ props.result.lunar.lunar_month }}月{{ props.result.lunar.lunar_day }}日</div>
    <div v-if="props.result.true_solar_time" class="pc-ct">真太阳时 {{ props.result.true_solar_time }}</div>
  </div>

  <div class="pc-divider"></div>

  <div class="pc-rulers">
    <span v-if="props.result.life_ruler_star" class="pc-cr-tag pc-cr-life">命·{{ props.result.life_ruler_star }}</span>
    <span v-if="props.result.body_ruler_star" class="pc-cr-tag pc-cr-body">身·{{ props.result.body_ruler_star }}</span>
  </div>

  <div v-if="props.result.dayun" class="pc-dayun-info">
    <span class="pc-dayun-dir">{{ props.result.dayun.forward ? '顺行' : '逆行' }}</span>
    <span class="pc-dayun-age">{{ props.result.dayun.start_age_text || `${props.result.dayun.start_age}岁起运` }}</span>
  </div>

  <div v-if="props.result.dayun?.items?.length" class="pc-dayun-strip">
    <div class="pc-dayun-ages">
      <span
        v-for="item in props.result.dayun.items"
        :key="item.index"
        :class="['pc-dys-age', { 'pc-dys-cur': isCurrentDayun(item.start_year) }]"
      >
        {{ item.start_age }}
      </span>
    </div>
    <div class="pc-dayun-years">
      <span
        v-for="item in props.result.dayun.items"
        :key="item.index"
        :class="['pc-dys-year', { 'pc-dys-cur': isCurrentDayun(item.start_year) }]"
      >
        {{ item.start_year }}
      </span>
    </div>
  </div>

  <div class="pc-ops-btns">
    <button class="pc-op-btn" title="前一天" @click="emit('shiftDay', -1)">日↑</button>
    <button class="pc-op-btn" title="后一天" @click="emit('shiftDay', 1)">日↓</button>
    <button class="pc-op-btn pc-op-tray" title="返回天盘" @click="emit('returnChart')">天盘▽</button>
    <button class="pc-op-btn" title="前一时辰" @click="emit('shiftHour', -1)">时↑</button>
    <button class="pc-op-btn" title="后一时辰" @click="emit('shiftHour', 1)">时↓</button>
  </div>

  <div v-if="props.result.flying?.self_transforms?.length" class="pc-zihua-row">
    <span class="pc-zihua-label">自化图示：</span>
    <span
      v-for="item in props.result.flying.self_transforms"
      :key="item"
      :class="['pc-zihua-tag', item.includes('禄') ? 'zh-lu' : item.includes('权') ? 'zh-quan' : item.includes('科') ? 'zh-ke' : 'zh-ji']"
    >
      {{ item }}
    </span>
  </div>
  <div v-else class="pc-zihua-row pc-zihua-hint">
    <span class="pc-zihua-label">自化图示：</span>
    <span class="pc-zihua-none">→禄</span>
    <span class="pc-zihua-none">→权</span>
    <span class="pc-zihua-none">→科</span>
    <span class="pc-zihua-none">→忌</span>
  </div>
</template>

<style scoped>
.pc-center-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.pc-cj {
  font-size: 18px;
  font-weight: 900;
  font-family: var(--font-cn);
  letter-spacing: 1px;
}

.pc-cg-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(120, 113, 108, 0.12);
  color: #57534e;
  font-weight: 600;
}

.pc-sizhu {
  display: flex;
  gap: 8px;
  margin: 4px 0;
}

.pc-sizhu-alt {
  margin-top: 2px;
  opacity: 0.65;
}

.pc-sz-item {
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-cn);
  color: #44403c;
  padding: 2px 6px;
  background: rgba(214, 201, 179, 0.3);
  border-radius: 4px;
}

.pc-sz-alt {
  background: rgba(214, 201, 179, 0.15);
  color: #78716c;
  font-weight: 500;
  font-size: 11px;
}

.pc-sz-hour {
  color: #78716c;
  font-weight: 600;
}

.pc-divider {
  width: 60%;
  height: 1px;
  background: #d6c9b3;
  margin: 2px 0;
}

.pc-birth-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pc-cb {
  font-size: 11px;
  color: #57534e;
}

.pc-cl {
  font-size: 10px;
  color: #78716c;
}

.pc-ct {
  font-size: 9px;
  color: #a8a29e;
}

.pc-rulers {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
  margin: 2px 0;
}

.pc-cr-tag {
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
}

.pc-cr-life {
  background: rgba(220,38,38,.12);
  color: #dc2626;
}

.pc-cr-body {
  background: rgba(37,99,235,.12);
  color: #2563eb;
}

.pc-dayun-info {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #78716c;
  margin-top: 2px;
}

.pc-dayun-dir {
  padding: 1px 5px;
  border-radius: 6px;
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
  font-weight: 600;
}

.pc-dayun-age {
  font-weight: 500;
}

.pc-dayun-strip {
  width: 100%;
  margin-top: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.pc-dayun-strip::-webkit-scrollbar {
  display: none;
}

.pc-dayun-ages,
.pc-dayun-years {
  display: flex;
  gap: 2px;
  width: max-content;
}

.pc-dys-age,
.pc-dys-year {
  font-size: 9px;
  color: #a8a29e;
  padding: 1px 4px;
  min-width: 24px;
  text-align: center;
}

.pc-dys-cur.pc-dys-age {
  color: #dc2626;
  font-weight: 700;
}

.pc-dys-cur.pc-dys-year {
  color: #dc2626;
  font-weight: 600;
}

.pc-ops-btns {
  display: flex;
  gap: 4px;
  margin-top: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.pc-op-btn {
  padding: 3px 8px;
  font-size: 10px;
  font-family: var(--font-cn);
  background: #e7e5e4;
  border: 1px solid #d6d3d1;
  border-radius: 4px;
  color: #57534e;
  cursor: pointer;
  transition: background 0.15s;
}

.pc-op-btn:hover {
  background: #d6d3d1;
  color: #292524;
}

.pc-op-tray {
  background: #f0fdf4;
  border-color: #86efac;
  color: #16a34a;
}

.pc-op-tray:hover {
  background: #dcfce7;
}

.pc-zihua-row {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-top: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.pc-zihua-label {
  font-size: 9px;
  color: #a8a29e;
}

.pc-zihua-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 3px;
}

.zh-lu {
  color: #16a34a;
}

.zh-quan {
  color: #ea580c;
}

.zh-ke {
  color: #2563eb;
}

.zh-ji {
  color: #dc2626;
}

.pc-zihua-none {
  font-size: 9px;
  color: #d6d3d1;
}

@media print {
  .pc-cj {
    font-size: 14pt;
    font-weight: bold;
  }

  .pc-cb,
  .pc-cl {
    font-size: 9pt;
    color: #333;
  }
}
</style>