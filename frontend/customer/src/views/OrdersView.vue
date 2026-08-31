<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import OrderCard from '../components/OrderCard.vue'

// 현재 세션 주문 내역 (3.1.5, frontend-components.md §4.4).
// 진입 시 재조회(Q6).
const router = useRouter()

const orders = ref([])
const loading = ref(false)
const error = ref('')

async function fetchOrders() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.orders(1, 50)
    orders.value = data.items || []
  } catch (e) {
    error.value = e.message || '주문 내역을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchOrders)
</script>

<template>
  <div class="page orders-view" data-testid="orders-view">
    <header class="topbar">
      <button class="ghost" @click="router.push({ name: 'menu' })" data-testid="nav-back">← 메뉴</button>
      <span class="title">주문 내역</span>
      <button class="ghost" @click="fetchOrders" data-testid="btn-refresh" aria-label="새로고침">↻</button>
    </header>

    <p v-if="loading" class="hint" data-testid="orders-loading">불러오는 중…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <div v-else-if="orders.length === 0" class="empty" data-testid="orders-empty">주문 내역이 없습니다.</div>
    <template v-else>
      <OrderCard v-for="o in orders" :key="o.order_id" :order="o" />
    </template>
  </div>
</template>
