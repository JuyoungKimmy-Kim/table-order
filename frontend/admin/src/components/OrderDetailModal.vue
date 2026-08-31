<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import StatusControl from './StatusControl.vue'

const props = defineProps({ orderId: { type: Number, required: true } })
defineEmits(['close'])

const detail = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    detail.value = await api.get(`/admin/orders/${props.orderId}`)
  } catch (e) {
    error.value = e.status === 404 ? '주문을 찾을 수 없습니다.' : '주문 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
})

function onStatusUpdated(next) {
  if (detail.value) detail.value.status = next
}
function won(n) { return `${(n ?? 0).toLocaleString('ko-KR')}원` }
</script>

<template>
  <div class="backdrop" @click.self="$emit('close')">
    <div class="modal">
      <button class="close" @click="$emit('close')">✕</button>
      <div v-if="loading">불러오는 중…</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="detail">
        <h2>{{ detail.order_number }}</h2>
        <p class="meta">테이블 {{ detail.table_number }} · {{ won(detail.total_amount) }}</p>
        <table class="items">
          <thead><tr><th>메뉴</th><th>단가</th><th>수량</th><th>금액</th></tr></thead>
          <tbody>
            <tr v-for="(it, i) in detail.items" :key="i">
              <td>{{ it.menu_name }}</td>
              <td>{{ won(it.unit_price) }}</td>
              <td>{{ it.quantity }}</td>
              <td>{{ won(it.line_total) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="status-row">
          <span>상태 변경</span>
          <StatusControl :order-id="detail.order_id" :status="detail.status"
                         @updated="onStatusUpdated" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 10px; padding: 20px; width: 460px; max-width: 92vw;
  position: relative; }
.close { position: absolute; top: 12px; right: 12px; border: 0; background: transparent;
  font-size: 16px; cursor: pointer; }
.modal h2 { margin: 0 0 4px; font-size: 18px; }
.meta { color: #666; margin: 0 0 12px; }
.items { width: 100%; border-collapse: collapse; font-size: 14px; }
.items th, .items td { text-align: left; padding: 6px 4px; border-bottom: 1px solid #eee; }
.items td:nth-child(n+2), .items th:nth-child(n+2) { text-align: right; }
.status-row { display: flex; align-items: center; gap: 12px; margin-top: 16px; }
.error { color: #dc2626; }
</style>
