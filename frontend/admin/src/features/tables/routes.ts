// Unit 4: 라우트 정의 (배열 export)
//
// CONTRACT-GAP: 계약은 프론트 라우팅을 정의하지 않는다. 유닛 정의서만 "별도 라우트로 분리".
// 자체 라우터를 만들지 않고 RouteRecordRaw[] 를 export 하여, 공유 admin 골격의 단일
// 라우터가 흡수하도록 한다(공유 router 파일 직접 수정 회피 → 충돌 0).
//
// INTEGRATION-TODO(admin-scaffold): 공유 router/index.ts 에서 아래처럼 흡수 —
//   import { tableRoutes } from '@/features/tables/routes'
//   const routes = [ ...monitoringRoutes, ...tableRoutes, ...menuRoutes ]
// 경로는 제안값이며 팀 조율 대상. 상세: frontend-integration-spec.md §2.3, §2.4

import type { RouteRecordRaw } from 'vue-router'

export const tableRoutes: RouteRecordRaw[] = [
  {
    path: '/tables/setup',
    name: 'table-setup',
    component: () => import('./TableSetupView.vue'),
    meta: { requiresAuth: true, unit: 'unit4' },
  },
  {
    path: '/tables/:tableId/orders',
    name: 'table-orders',
    component: () => import('./TableOrdersView.vue'),
    props: true,
    meta: { requiresAuth: true, unit: 'unit4' },
  },
  {
    path: '/tables/:tableId/history',
    name: 'table-history',
    component: () => import('./OrderHistoryView.vue'),
    props: true,
    meta: { requiresAuth: true, unit: 'unit4' },
  },
]
