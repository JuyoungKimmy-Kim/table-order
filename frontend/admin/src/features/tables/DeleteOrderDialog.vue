<script setup lang="ts">
// Unit 4: 주문 직권 삭제 확인 팝업 (요구 3.2.3-2)
// 프레젠테이션 전용. API 호출은 부모(TableOrdersView)가 수행한다.
import type { OrderDetail } from './types'

defineProps<{ order: OrderDetail }>()
const emit = defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>

<template>
  <div class="backdrop" @click.self="emit('cancel')">
    <div class="dialog" role="dialog" aria-modal="true">
      <h3>주문 삭제</h3>
      <p>
        주문 <strong>{{ order.order_number }}</strong> (총
        {{ order.total_amount.toLocaleString() }}원)을 삭제하시겠습니까?
      </p>
      <p class="warn">삭제 시 테이블 총 주문액이 즉시 재계산됩니다.</p>
      <div class="actions">
        <button class="ghost" @click="emit('cancel')">취소</button>
        <button class="danger" @click="emit('confirm')">삭제</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; }
.dialog { background: #fff; padding: 24px; border-radius: 10px; max-width: 360px; width: 90%; }
.warn { font-size: 13px; color: #b45309; }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
button { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; }
.ghost { background: #f3f4f6; }
.danger { background: #dc2626; color: #fff; }
</style>
