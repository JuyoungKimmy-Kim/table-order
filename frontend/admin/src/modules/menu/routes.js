// Unit 5: 메뉴 관리 라우트 정의 (Vue Router).
// Unit 3(임동규)의 관리자 앱 셸 라우터에 병합한다:
//
//   import menuRoutes from '@/modules/menu/routes.js'
//   const routes = [ { path: '/', component: AdminLayout, meta: { requiresAuth: true },
//                      children: [ ...menuRoutes, /* Unit 3/4 라우트 */ ] } ]
//
// 인증 가드(requiresAuth)와 레이아웃은 Unit 3 소유. 여기서는 메뉴 모듈 화면만 노출한다.

const menuRoutes = [
  {
    path: 'menus',
    name: 'admin-menus',
    component: () => import('./views/MenuListView.vue'),
    meta: { title: '메뉴 관리', requiresAuth: true },
  },
  {
    path: 'menu-categories',
    name: 'admin-menu-categories',
    component: () => import('./views/CategoryManageView.vue'),
    meta: { title: '카테고리 관리', requiresAuth: true },
  },
]

export default menuRoutes
