<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMenuStore } from '../stores/menu'
import { useCartStore } from '../stores/cart'
import { useSessionStore } from '../stores/session'
import CategoryTabs from '../components/CategoryTabs.vue'
import MenuGrid from '../components/MenuGrid.vue'
import MenuDetailModal from '../components/MenuDetailModal.vue'
import CartFab from '../components/CartFab.vue'

// 메뉴 화면(기본, 3.1.2). 카드 클릭 → 상세 모달(Q3).
const menu = useMenuStore()
const cart = useCartStore()
const session = useSessionStore()
const router = useRouter()

const selected = ref(null)
const activeMenus = computed(() => menu.activeMenus)

onMounted(() => {
  cart.load()
  menu.fetchMenus()
})

function openDetail(m) {
  selected.value = m
}
function addToCart(m, qty) {
  cart.add(m, qty)
  selected.value = null
}
</script>

<template>
  <div class="page menu-view" data-testid="menu-view">
    <header class="topbar">
      <span class="title">{{ session.storeName }} · {{ session.tableNumber }}번</span>
      <button class="ghost" @click="router.push({ name: 'orders' })" data-testid="nav-orders">주문내역</button>
    </header>

    <p v-if="menu.loading" class="hint" data-testid="menu-loading">메뉴 불러오는 중…</p>
    <p v-else-if="menu.error" class="error">{{ menu.error }}</p>
    <template v-else>
      <CategoryTabs
        :categories="menu.categories"
        :active-id="menu.activeCategoryId"
        @select="menu.setActiveCategory"
      />
      <MenuGrid :menus="activeMenus" @open="openDetail" />
    </template>

    <MenuDetailModal v-if="selected" :menu="selected" @add="addToCart" @close="selected = null" />
    <CartFab :count="cart.itemCount" :total="cart.totalAmount" @click="router.push({ name: 'cart' })" />
  </div>
</template>
