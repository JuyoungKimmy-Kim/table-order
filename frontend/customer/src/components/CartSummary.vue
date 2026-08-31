<script setup>
defineProps({ total: { type: Number, default: 0 } })

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
</script>

<template>
  <div class="summary" data-testid="cart-summary">
    <span>합계</span>
    <strong data-testid="cart-total">{{ won(total) }}</strong>
  </div>
</template>
