<script setup>
defineProps({ order: { type: Object, required: true } })

const STATUS = {
  pending: '대기중',
  preparing: '준비중',
  completed: '완료',
  served: '완료',
  cancelled: '취소',
}

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
function statusLabel(s) {
  return STATUS[s] || s
}
</script>

<template>
  <div class="order-card" :data-testid="`order-card-${order.order_id}`">
    <div class="head">
      <strong>{{ order.order_number }}</strong>
      <span class="status" :class="order.status" :data-testid="`order-status-${order.order_id}`">
        {{ statusLabel(order.status) }}
      </span>
    </div>
    <div class="time">{{ order.ordered_at }}</div>
    <ul class="items">
      <li v-for="(it, i) in order.items" :key="i">
        {{ it.menu_name }} × {{ it.quantity }}
        <span class="line">{{ won(it.line_total ?? it.unit_price * it.quantity) }}</span>
      </li>
    </ul>
    <div class="total">
      <span>합계</span>
      <strong>{{ won(order.total_amount) }}</strong>
    </div>
  </div>
</template>
