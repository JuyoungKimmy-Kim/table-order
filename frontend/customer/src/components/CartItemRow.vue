<script setup>
defineProps({ item: { type: Object, required: true } })
defineEmits(['inc', 'dec', 'remove'])

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
</script>

<template>
  <div class="cart-row" :class="{ unavailable: item.unavailable }" :data-testid="`cart-row-${item.menu_id}`">
    <div class="info">
      <span class="name">{{ item.name }}</span>
      <span v-if="item.unavailable" class="badge-soldout" data-testid="soldout-badge">품절</span>
      <span class="price">{{ won(item.price) }}</span>
    </div>
    <div class="qty">
      <button data-testid="row-dec" aria-label="수량 감소" @click="$emit('dec')">−</button>
      <span data-testid="row-qty">{{ item.quantity }}</span>
      <button data-testid="row-inc" aria-label="수량 증가" @click="$emit('inc')">＋</button>
      <button class="remove" data-testid="row-remove" aria-label="삭제" @click="$emit('remove')">🗑</button>
    </div>
  </div>
</template>
