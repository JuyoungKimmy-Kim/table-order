import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from '../stores/session'

// 라우트 (frontend-components.md §1). 기본 화면 = 메뉴('/').
const routes = [
  { path: '/setup', name: 'setup', component: () => import('../views/SetupView.vue'), meta: { public: true } },
  { path: '/', name: 'menu', component: () => import('../views/MenuView.vue') },
  { path: '/cart', name: 'cart', component: () => import('../views/CartView.vue') },
  { path: '/orders', name: 'orders', component: () => import('../views/OrdersView.vue') },
  { path: '/guestbook', name: 'guestbook', component: () => import('../views/GuestbookView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 네비게이션 가드: 미인증 → /setup (BR-C1.4). 인증 상태로 /setup 진입 → 메뉴.
router.beforeEach((to) => {
  const session = useSessionStore()
  if (!to.meta.public && !session.isAuthenticated) {
    return { name: 'setup' }
  }
  if (to.name === 'setup' && session.isAuthenticated) {
    return { name: 'menu' }
  }
})

export default router
