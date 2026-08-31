<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGuestbookStore } from '../stores/guestbook'
import GuestbookCard from '../components/GuestbookCard.vue'
import DrawingModal from '../components/DrawingModal.vue'

// 방명록 화면: 매장 공유 카드 그리드 + 그림판 모달로 작성.
const router = useRouter()
const guestbook = useGuestbookStore()
const showModal = ref(false)

onMounted(() => guestbook.fetch())

async function onSave({ imageData, authorName }) {
  try {
    await guestbook.create({ imageData, authorName })
    showModal.value = false
  } catch {
    // 에러는 store.error 로 노출됨(모달 유지).
  }
}
</script>

<template>
  <div class="page guestbook-view" data-testid="guestbook-view">
    <header class="topbar">
      <button class="ghost" @click="router.push({ name: 'menu' })" data-testid="nav-back">← 메뉴</button>
      <span class="title">방명록</span>
      <button class="ghost" @click="guestbook.fetch" aria-label="새로고침">↻</button>
    </header>

    <p v-if="guestbook.error" class="error">{{ guestbook.error }}</p>
    <p v-if="guestbook.loading" class="hint" data-testid="guestbook-loading">불러오는 중…</p>
    <div v-else-if="guestbook.entries.length === 0" class="empty" data-testid="guestbook-empty">
      아직 방명록이 없습니다.<br />첫 방명록을 남겨보세요!
    </div>
    <div v-else class="gb-grid">
      <GuestbookCard v-for="e in guestbook.entries" :key="e.id" :entry="e" />
    </div>

    <button class="fab" @click="showModal = true" data-testid="btn-open-drawing">✏️ 방명록 남기기</button>

    <DrawingModal
      v-if="showModal"
      :saving="guestbook.saving"
      @save="onSave"
      @close="showModal = false"
    />
  </div>
</template>
