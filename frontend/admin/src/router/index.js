import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
// Unit 4: 테이블/세션 라우트를 배열로 흡수(공유 라우터가 단일 소유). routes.ts §2.3
import { tableRoutes } from '../features/tables/routes'
// Unit 5: 메뉴 관리 라우트. routes.js 는 children(상대경로) 전제이나 현 셸은 flat 구조라
// 절대경로로 정규화하여 흡수한다(path 앞에 '/' 부여).
import menuRoutes from '../modules/menu/routes.js'

const normalizedMenuRoutes = menuRoutes.map((r) => ({
  ...r,
  path: r.path.startsWith('/') ? r.path : `/${r.path}`,
}))

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
  { path: '/', name: 'dashboard', component: DashboardView },
  ...tableRoutes,
  ...normalizedMenuRoutes,
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 인증 가드(3.2.1): 미인증 → /login, 인증 상태에서 /login 접근 → /
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
