<script setup>
import MenuCard from './MenuCard.vue'

defineProps({ menus: { type: Array, default: () => [] } })
defineEmits(['open'])
</script>

<template>
  <div class="grid" data-testid="menu-grid">
    <MenuCard v-for="m in menus" :key="m.id" :menu="m" @open="$emit('open', m)" />
    <p v-if="!menus.length" class="hint" data-testid="menu-empty">이 카테고리에 메뉴가 없습니다.</p>
  </div>
</template>
