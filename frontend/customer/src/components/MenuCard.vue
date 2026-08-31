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
      <span class="card-add" aria-hidden="true">＋</span>
    </div>
    <div class="body">
      <div class="name">{{ menu.name }}</div>
      <p v-if="menu.description" class="desc">{{ menu.description }}</p>
      <div class="price">{{ won(menu.price) }}</div>
    </div>
  </button>
</template>
