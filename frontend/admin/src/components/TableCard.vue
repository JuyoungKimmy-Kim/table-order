<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({ card: { type: Object, required: true } })
defineEmits(['open-order'])

// Q6=A: highlightUntil 이 미래면 강조. 시간 경과에 맞춰 갱신.
const now = ref(Date.now())
let timer
onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 500) })
onUnmounted(() => clearInterval(timer))

const highlighted = computed(() =>
  props.card.highlightUntil && now.value < props.card.highlightUntil)

const statusLabel = { pending: '대기중', preparing: '준비중', completed: '완료' }
function won(n) { return `${(n ?? 0).toLocaleString('ko-KR')}원` }
</script>

<template>
  <div class="card" :class="{ highlight: highlighted, inactive: !card.session_active }">
    <div class="head">
      <span class="tno">테이블 {{ card.table_number }}</span>
      <span class="total">{{ won(card.table_total) }}</span>
    </div>
    <div v-if="!card.session_active" class="empty">이용 중 아님</div>
    <ul v-else class="orders">
      <li v-for="o in card.recent_orders" :key="o.order_id"
          class="order" @click="$emit('open-order', o.order_id)">
        <span class="onum">{{ o.order_number }}</span>
        <span class="prev">{{ o.item_preview }}</span>
        <span class="st" :class="o.status">{{ statusLabel[o.status] || o.status }}</span>
      </li>
      <li v-if="!card.recent_orders?.length" class="empty">주문 없음</li>
    </ul>
  </div>
</template>

<style scoped>
.card { background: #fff; border-radius: 10px; padding: 12px; box-shadow: 0 1px 6px rgba(0,0,0,.06);
  transition: box-shadow .2s, outline .2s; }
.card.inactive { opacity: .6; }
.card.highlight { outline: 3px solid #f59e0b; box-shadow: 0 0 14px rgba(245,158,11,.5); }
.head { display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 8px; }
.total { color: #2563eb; }
.orders { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.order { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; padding: 6px;
  border: 1px solid #eee; border-radius: 6px; cursor: pointer; font-size: 13px; }
.order:hover { background: #f9fafb; }
.onum { font-weight: 600; }
.prev { color: #666; grid-column: 1; }
.st { grid-row: 1 / span 2; align-self: center; font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.st.pending { background: #e5e7eb; }
.st.preparing { background: #fef3c7; color: #92400e; }
.st.completed { background: #dcfce7; color: #166534; }
.empty { color: #999; font-size: 13px; padding: 8px 0; }
</style>
