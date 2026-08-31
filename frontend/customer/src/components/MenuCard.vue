<script setup>
defineProps({ menu: { type: Object, required: true } })
defineEmits(['open'])

function won(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}
</script>

<template>
  <button class="card" :data-testid="`menu-card-${menu.id}`" @click="$emit('open')">
    <div class="thumb">
      <img v-if="menu.image_url" :src="menu.image_url" :alt="menu.name" />
      <span v-else class="placeholder">🍽️</span>
    </div>
    <div class="name">{{ menu.name }}</div>
    <div class="price">{{ won(menu.price) }}</div>
  </button>
</template>
