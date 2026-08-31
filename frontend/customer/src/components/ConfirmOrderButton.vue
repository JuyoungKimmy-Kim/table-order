<script setup>
defineProps({
  disabled: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
})
defineEmits(['submit'])
</script>

<template>
  <button
    class="primary order-btn"
    :disabled="disabled"
    data-testid="btn-submit-order"
    @click="$emit('submit')"
  >
    {{ submitting ? '주문 중…' : '주문하기' }}
  </button>
</template>
