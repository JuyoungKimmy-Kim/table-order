<script setup>
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'

// Q7=A: 클라이언트 측 필터. 서버 요청 없음.
const dashboard = useDashboardStore()

const status = computed({
  get: () => dashboard.filter.status ?? '',
  set: (v) => dashboard.setFilter({ status: v || null }),
})
const tableNumber = computed({
  get: () => dashboard.filter.tableNumber ?? '',
  set: (v) => dashboard.setFilter({ tableNumber: v === '' ? null : Number(v) }),
})
</script>

<template>
  <div class="filter">
    <label>상태
      <select v-model="status">
        <option value="">전체</option>
        <option value="pending">대기중</option>
        <option value="preparing">준비중</option>
        <option value="completed">완료</option>
      </select>
    </label>
    <label>테이블 번호
      <input v-model="tableNumber" type="number" min="1" placeholder="전체" />
    </label>
  </div>
</template>

<style scoped>
.filter { display: flex; gap: 16px; align-items: center; margin-top: 8px; font-size: 13px; }
.filter select, .filter input { padding: 4px 8px; margin-left: 4px; }
.filter input { width: 80px; }
</style>
