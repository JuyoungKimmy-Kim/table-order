<script setup lang="ts">
// Unit 4: 테이블 현재 주문 관리 (요구 3.2.3-2, §3.3.4)
// - 현재 세션 미삭제 주문 목록 + 테이블 총액
// - 주문 직권 삭제(DeleteOrderDialog) → 총액 즉시 재계산
// - 이용 완료(CloseSessionDialog) → 세션 종료 후 목록 초기화
import { computed, onMounted, ref } from 'vue'
import { closeSession, deleteOrder, getCurrentOrders } from './api'
import { ApiError } from './http'
import type { OrderDetail } from './types'
import DeleteOrderDialog from './DeleteOrderDialog.vue'
import CloseSessionDialog from './CloseSessionDialog.vue'

// routes.ts 에서 props:true 로 전달되는 라우트 파라미터.
const props = defineProps<{ tableId: string }>()
const tableId = computed(() => Number(props.tableId))

const orders = ref<OrderDetail[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// 삭제 대상 / 세션 종료 확인 다이얼로그 상태
const pendingDelete = ref<OrderDetail | null>(null)
const showClose = ref(false)
const busy = ref(false)

// 테이블 총액은 서버(§3.3.2 table_total)가 SSOT이지만, 초기 표시는 클라이언트 합산.
const tableTotal = computed(() => orders.value.reduce((sum, o) => sum + o.total_amount, 0))
const tableNumber = computed(() => orders.value[0]?.table_number ?? tableId.value)

async function load() {
  loading.value = true
  error.value = null
  try {
    orders.value = await getCurrentOrders(tableId.value)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '주문 목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function confirmDelete() {
  if (!pendingDelete.value) return
  busy.value = true
  error.value = null
  try {
    await deleteOrder(pendingDelete.value.order_id)
    pendingDelete.value = null
    // 서버가 재계산한 상태를 신뢰하기 위해 재조회.
    await load()
  } catch (e) {
    // 이미 삭제된 주문(멱등) 등은 성공에 준함 → 재조회로 정합성 확보.
    error.value = e instanceof ApiError ? e.message : '주문 삭제에 실패했습니다.'
    pendingDelete.value = null
  } finally {
    busy.value = false
  }
}

async function confirmClose() {
  busy.value = true
  error.value = null
  try {
    await closeSession(tableId.value)
    showClose.value = false
    orders.value = []
  } catch (e) {
    // NO_ACTIVE_SESSION 등은 이미 종료된 상태 → 목록 비우고 메시지 표시.
    error.value = e instanceof ApiError ? e.message : '이용 완료 처리에 실패했습니다.'
    showClose.value = false
    await load()
  } finally {
    busy.value = false
  }
}

// INTEGRATION-TODO(unit2-sse): Unit 2/1의 SSE 클라이언트가 붙으면 order.deleted /
// session.closed 구독으로 실시간 갱신 가능. 현재는 액션 후 재조회로 대체.
// 상세: frontend-integration-spec.md
onMounted(load)
</script>

<template>
  <section class="table-orders">
    <header class="head">
      <h2>{{ tableNumber }}번 테이블 · 현재 주문</h2>
      <div class="total">총 주문액 <strong>{{ tableTotal.toLocaleString() }}원</strong></div>
    </header>

    <div class="toolbar">
      <button class="refresh" :disabled="loading" @click="load">새로고침</button>
      <button class="close-session" :disabled="busy || orders.length === 0" @click="showClose = true">
        이용 완료
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="muted">불러오는 중…</p>
    <p v-else-if="orders.length === 0" class="muted">현재 세션에 주문이 없습니다.</p>

    <ul v-else class="order-list">
      <li v-for="o in orders" :key="o.order_id" class="order">
        <div class="order-head">
          <span class="num">{{ o.order_number }}</span>
          <span class="status">{{ o.status }}</span>
          <span class="amount">{{ o.total_amount.toLocaleString() }}원</span>
          <button class="del" :disabled="busy" @click="pendingDelete = o">삭제</button>
        </div>
        <ul class="items">
          <li v-for="(it, i) in o.items" :key="i">
            {{ it.menu_name }} × {{ it.quantity }} = {{ it.line_total.toLocaleString() }}원
          </li>
        </ul>
      </li>
    </ul>

    <DeleteOrderDialog
      v-if="pendingDelete"
      :order="pendingDelete"
      @confirm="confirmDelete"
      @cancel="pendingDelete = null"
    />
    <CloseSessionDialog
      v-if="showClose"
      :table-number="tableNumber"
      :order-count="orders.length"
      @confirm="confirmClose"
      @cancel="showClose = false"
    />
  </section>
</template>

<style scoped>
.table-orders { max-width: 640px; }
.head { display: flex; justify-content: space-between; align-items: baseline; }
.total strong { font-size: 18px; }
.toolbar { display: flex; gap: 8px; margin: 12px 0; }
button { padding: 8px 14px; border: none; border-radius: 6px; cursor: pointer; }
.refresh { background: #f3f4f6; }
.close-session { background: #059669; color: #fff; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.order-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.order { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.order-head { display: flex; align-items: center; gap: 12px; }
.num { font-weight: 600; }
.status { font-size: 12px; color: #6b7280; text-transform: uppercase; }
.amount { margin-left: auto; }
.del { background: #fef2f2; color: #b91c1c; padding: 4px 10px; }
.items { margin: 8px 0 0; padding-left: 18px; font-size: 13px; color: #374151; }
.error { color: #b91c1c; }
.muted { color: #6b7280; }
</style>
