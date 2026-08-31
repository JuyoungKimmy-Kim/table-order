<script setup>
import { ref } from 'vue'

const props = defineProps({ menu: { type: Object, required: true } })
const emit = defineEmits(['add', 'close'])

const qty = ref(1)

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
function dec() {
  if (qty.value > 1) qty.value--
}
function inc() {
  qty.value++
}
</script>

<template>
  <div class="modal-overlay" data-testid="menu-detail-modal" @click.self="emit('close')">
    <div class="modal">
      <button class="close" data-testid="modal-close" aria-label="닫기" @click="emit('close')">✕</button>
      <div class="thumb-lg">
        <img v-if="menu.image_url" :src="menu.image_url" :alt="menu.name" />
        <span v-else class="placeholder">🍽️</span>
      </div>
      <h2 class="name">{{ menu.name }}</h2>
      <p v-if="menu.description" class="desc">{{ menu.description }}</p>
      <p class="price">{{ won(menu.price) }}</p>
      <div class="stepper">
        <button data-testid="qty-dec" aria-label="수량 감소" @click="dec">−</button>
        <span data-testid="qty-value">{{ qty }}</span>
        <button data-testid="qty-inc" aria-label="수량 증가" @click="inc">＋</button>
      </div>
      <button class="primary" data-testid="btn-add-cart" @click="emit('add', menu, qty)">
        장바구니 담기 · {{ won(menu.price * qty) }}
      </button>
    </div>
  </div>
</template>
