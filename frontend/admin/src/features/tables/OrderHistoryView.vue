<script setup lang="ts">
// Unit 4: 과거 주문 내역 조회 (요구 3.2.3-4, §3.3.5)
// - 날짜 필터(date_from/date_to, YYYY-MM-DD)
// - 최신순 페이지네이션(§0.4 Paginated)
import { computed, onMounted, ref } from 'vue'
import { getHistory } from './api'
import { ApiError } from './http'
import type { HistoryOrderDetail } from './types'

const props = defineProps<{ tableId: string }>()
const tableId = computed(() => Number(props.tableId))

const dateFrom = ref('')
const dateTo = ref('')
const page = ref(1)
const size = ref(20)

const rows = ref<HistoryOrderDetail[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size.value)))

async function load() {
  loading.value = true
  error.value = null
  try {
    const res = await getHistory(tableId.value, {
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      page: page.value,
      size: size.value,
    })
    rows.value = res.items
    total.value = res.total
    page.value = res.page
    size.value = res.size
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '내역을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

// 필터 적용 시 첫 페이지부터.
function applyFilter() {
  page.value = 1
  load()
}

function goPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  load()
}

// UTC ISO → 로컬 표시(간단 변환).
function fmt(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

onMounted(load)
</script>

<template>
  <section class="history">
    <h2>{{ tableId }}번 테이블 · 과거 주문 내역</h2>

    <form class="filter" @submit.prevent="applyFilter">
      <label>시작일 <input v-model="dateFrom" type="date" /></label>
      <label>종료일 <input v-model="dateTo" type="date" /></label>
      <button type="submit" :disabled="loading">조회</button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="muted">불러오는 중…</p>
    <p v-else-if="rows.length === 0" class="muted">조회된 내역이 없습니다.</p>

    <ul v-else class="rows">
      <li v-for="o in rows" :key="o.order_id" class="row">
        <div class="row-head">
          <span class="num">{{ o.order_number }}</span>
          <span class="amount">{{ o.total_amount.toLocaleString() }}원</span>
        </div>
        <div class="meta">
          주문 {{ fmt(o.ordered_at) }} · 세션종료 {{ fmt(o.session_closed_at) }}
        </div>
        <ul class="items">
          <li v-for="(it, i) in o.items" :key="i">
            {{ it.menu_name }} × {{ it.quantity }} = {{ it.line_total.toLocaleString() }}원
          </li>
        </ul>
      </li>
    </ul>

    <nav v-if="rows.length > 0" class="pager">
      <button :disabled="page <= 1 || loading" @click="goPage(page - 1)">이전</button>
      <span>{{ page }} / {{ totalPages }} (총 {{ total }}건)</span>
      <button :disabled="page >= totalPages || loading" @click="goPage(page + 1)">다음</button>
    </nav>
  </section>
</template>

<style scoped>
.history { max-width: 640px; }
.filter { display: flex; gap: 12px; align-items: flex-end; margin: 12px 0; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
input { padding: 6px; border: 1px solid #ccc; border-radius: 6px; }
button { padding: 8px 14px; border: none; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.rows { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.row { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.row-head { display: flex; justify-content: space-between; font-weight: 600; }
.meta { font-size: 12px; color: #6b7280; margin: 4px 0; }
.items { margin: 4px 0 0; padding-left: 18px; font-size: 13px; color: #374151; }
.pager { display: flex; align-items: center; gap: 12px; justify-content: center; margin-top: 16px; }
.pager span { font-size: 13px; color: #374151; }
.error { color: #b91c1c; }
.muted { color: #6b7280; }
</style>
