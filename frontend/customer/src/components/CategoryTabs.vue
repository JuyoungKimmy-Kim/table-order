<script setup>
defineProps({
  categories: { type: Array, default: () => [] },
  activeId: { type: [Number, null], default: null },
})
defineEmits(['select'])
</script>

<template>
  <nav class="tabs" data-testid="category-tabs">
    <button
      v-for="c in categories"
      :key="c.id"
      class="tab"
      :class="{ active: c.id === activeId }"
      :data-testid="`category-tab-${c.id}`"
      @click="$emit('select', c.id)"
    >
      {{ c.name }}
    </button>
  </nav>
</template>
