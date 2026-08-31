<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { api } from '../api/client'
import CartItemRow from '../components/CartItemRow.vue'
import CartSummary from '../components/CartSummary.vue'
import ConfirmOrderButton from '../components/ConfirmOrderButton.vue'
import OrderConfirmModal from '../components/OrderConfirmModal.vue'

// 장바구니/주문 확인 (3.1.3, 3.1.4, frontend-components.md §4.3).
const cart = useCartStore()
const router = useRouter()

const submitting = ref(false)
const error = ref('')
const confirmedOrderNumber = ref('')

onMounted(() => cart.load())

const hasUnavailable = computed(() => cart.items.some((it) => it.unavailable))
const canOrder = computed(() => cart.items.length > 0 && !hasUnavailable.value && !submitting.value)

async function submitOrder() {
  error.value = ''
  submitting.value = true
  try {
    const items = cart.items.map((it) => ({ menu_id: it.menu_id, quantity: it.quantity }))
    const res = await api.createOrder(items)
    confirmedOrderNumber.value = res.order_number // 성공 → 확인 모달
    cart.clear()
  } catch (e) {
    // 서버가 거부한 문제 메뉴를 품절 표시(Q5). 장바구니는 유지.
    if (e.code === 'MENU_UNAVAILABLE') {
      cart.markUnavailable(e.details?.unavailable_menu_ids || [])
      error.value = '일부 메뉴가 품절되었습니다. 확인 후 다시 주문해 주세요.'
    } else if (e.code === 'MENU_NOT_FOUND') {
      cart.markUnavailable(e.details?.not_found_menu_ids || [])
      error.value = '일부 메뉴를 찾을 수 없습니다.'
    } else {
      error.value = e.message || '주문에 실패했습니다.'
    }
  } finally {
    submitting.value = false
  }
}

function closeConfirm() {
  confirmedOrderNumber.value = ''
  router.push({ name: 'menu' })
}
</script>

<template>
  <div class="page cart-view" data-testid="cart-view">
    <header class="topbar">
      <button class="ghost" @click="router.push({ name: 'menu' })" data-testid="nav-back">← 메뉴</button>
      <span class="title">장바구니</span>
      <span />
    </header>

    <div v-if="cart.items.length === 0" class="empty" data-testid="cart-empty">
      장바구니가 비어 있습니다.
    </div>
    <template v-else>
      <CartItemRow
        v-for="it in cart.items"
        :key="it.menu_id"
        :item="it"
        @inc="cart.updateQty(it.menu_id, it.quantity + 1)"
        @dec="cart.updateQty(it.menu_id, it.quantity - 1)"
        @remove="cart.remove(it.menu_id)"
      />
      <p v-if="error" class="error" data-testid="cart-error">{{ error }}</p>
      <CartSummary :total="cart.totalAmount" />
      <ConfirmOrderButton :disabled="!canOrder" :submitting="submitting" @submit="submitOrder" />
    </template>

    <OrderConfirmModal
      v-if="confirmedOrderNumber"
      :order-number="confirmedOrderNumber"
      @close="closeConfirm"
    />
  </div>
</template>
