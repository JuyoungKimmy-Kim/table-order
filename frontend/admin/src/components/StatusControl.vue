<script setup>
import { ref } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  orderId: { type: Number, required: true },
  status: { type: String, required: true },
})
const emit = defineEmits(['updated'])

const busy = ref(false)
const error = ref('')

// Q4=A: 자유 전이 — 모든 상태 선택 가능(되돌리기 포함).
const options = [
  { value: 'pending', label: '대기중' },
  { value: 'preparing', label: '준비중' },
  { value: 'completed', label: '완료' },
]

async function change(next) {
  if (next === props.status || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const res = await api.patch(`/admin/orders/${props.orderId}/status`, { status: next })
    // 낙관적 확정은 SSE(order.status_changed)로 전 화면 동기화됨.
    emit('updated', res.status)
  } catch (e) {
    error.value = '상태 변경에 실패했습니다.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="status-control">
    <button
      v-for="opt in options"
      :key="opt.value"
      :class="{ active: opt.value === status }"
      :disabled="busy"
      @click="change(opt.value)"
    >{{ opt.label }}</button>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>

<style scoped>
.status-control { display: flex; gap: 8px; align-items: center; }
.status-control button { padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px;
  background: #fff; cursor: pointer; }
.status-control button.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.error { color: #dc2626; font-size: 12px; }
</style>
