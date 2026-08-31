<script setup>
import { computed } from 'vue'

// 방명록 카드 한 장: 그림 + 작성자명(선택) + 작성 시각.
const props = defineProps({
  entry: { type: Object, required: true }, // { id, author_name, image_data, created_at }
})

const authorLabel = computed(() => props.entry.author_name || '익명')
const timeLabel = computed(() => {
  const d = new Date(props.entry.created_at)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ko-KR', {
    month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
})
</script>

<template>
  <div class="gb-card" data-testid="guestbook-card">
    <div class="gb-thumb">
      <img :src="entry.image_data" :alt="`${authorLabel} 님의 방명록`" />
    </div>
    <div class="gb-meta">
      <span class="gb-author">{{ authorLabel }}</span>
      <span class="gb-time">{{ timeLabel }}</span>
    </div>
  </div>
</template>
