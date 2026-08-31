<script setup>
defineProps({ orderNumber: { type: String, required: true } })
defineEmits(['close'])
</script>

<template>
  <div class="modal-overlay" data-testid="order-confirm-modal">
    <div class="modal center">
      <div class="check">✅</div>
      <h2>주문 완료</h2>
      <p class="label">주문번호</p>
      <p class="order-no" data-testid="confirm-order-number">{{ orderNumber }}</p>
      <button class="primary" data-testid="btn-confirm-close" @click="$emit('close')">확인</button>
    </div>
  </div>
</template>
