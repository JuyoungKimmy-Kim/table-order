<script setup>
defineProps({
  count: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
})
defineEmits(['click'])

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
</script>

<template>
  <button v-if="count > 0" class="fab" data-testid="cart-fab" @click="$emit('click')">
    <span class="badge" data-testid="cart-count">{{ count }}</span>
    <span>장바구니</span>
    <strong>{{ won(total) }}</strong>
  </button>
</template>
