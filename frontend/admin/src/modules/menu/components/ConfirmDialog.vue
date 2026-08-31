<script setup>
// Unit 5: 삭제 확인 다이얼로그 (요구사항 3.2.3 "확인 팝업" 패턴 준용).
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '확인' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: '삭제' },
  danger: { type: Boolean, default: true },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <div v-if="open" class="cd-backdrop" @click.self="emit('cancel')">
    <div class="cd-dialog" role="dialog" aria-modal="true">
      <h3 class="cd-title">{{ title }}</h3>
      <p class="cd-message">{{ message }}</p>
      <div class="cd-actions">
        <button type="button" class="cd-btn" @click="emit('cancel')">취소</button>
        <button
          type="button"
          class="cd-btn"
          :class="danger ? 'cd-btn--danger' : 'cd-btn--primary'"
          @click="emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cd-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.cd-dialog {
  background: #fff; border-radius: 10px; padding: 24px; width: min(420px, 92vw);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
.cd-title { margin: 0 0 8px; font-size: 18px; }
.cd-message { margin: 0 0 20px; color: #444; line-height: 1.5; white-space: pre-line; }
.cd-actions { display: flex; justify-content: flex-end; gap: 8px; }
.cd-btn {
  padding: 8px 16px; border-radius: 6px; border: 1px solid #ccc;
  background: #f5f5f5; cursor: pointer; font-size: 14px;
}
.cd-btn--danger { background: #e5484d; border-color: #e5484d; color: #fff; }
.cd-btn--primary { background: #0b74de; border-color: #0b74de; color: #fff; }
</style>
