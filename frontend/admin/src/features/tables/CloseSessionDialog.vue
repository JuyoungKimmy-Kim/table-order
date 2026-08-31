<script setup lang="ts">
// Unit 4: 세션 종료(이용 완료) 확인 팝업 (요구 3.2.3-3)
// 프레젠테이션 전용. API 호출은 부모(TableOrdersView)가 수행한다.
defineProps<{ tableNumber: number; orderCount: number }>()
const emit = defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>

<template>
  <div class="backdrop" @click.self="emit('cancel')">
    <div class="dialog" role="dialog" aria-modal="true">
      <h3>이용 완료 처리</h3>
      <p>
        <strong>{{ tableNumber }}번 테이블</strong>의 이용을 완료하시겠습니까?
      </p>
      <p class="warn">
        현재 세션의 주문 {{ orderCount }}건이 과거 내역으로 이동하고, 테이블 현재 주문·총액이 0으로
        초기화됩니다. (되돌릴 수 없음)
      </p>
      <div class="actions">
        <button class="ghost" @click="emit('cancel')">취소</button>
        <button class="primary" @click="emit('confirm')">이용 완료</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; }
.dialog { background: #fff; padding: 24px; border-radius: 10px; max-width: 380px; width: 90%; }
.warn { font-size: 13px; color: #b45309; }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
button { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
.ghost { background: #f3f4f6; }
.primary { background: #2563eb; color: #fff; }
</style>
