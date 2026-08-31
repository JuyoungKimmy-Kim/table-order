// Unit 4: 관리자 인증 토큰 브리지 (임시 shim)
//
// CONTRACT-GAP: Integration Contract §0.3 은 "Authorization: Bearer <JWT>" 규약만
// 정의하고, 토큰을 어디서 얻는지는 정의하지 않는다. 로그인/토큰 발급은 Unit 3(§3.2.1) 소유.
//
// 병렬 개발 중이라 Unit 3 의 auth store 가 아직 없으므로, 개발용 stopgap 으로
// localStorage 의 토큰을 읽는다. Unit 3 완성 후 아래 getAdminToken() 본문만 교체하면
// 나머지 코드(api.ts/http.ts)는 변경 없이 동작한다.
//
// INTEGRATION-TODO(unit3-auth): 교체 예시 —
//   import { useAuthStore } from '@/stores/auth'   // Unit 3 제공(예정)
//   export function getAdminToken() { return useAuthStore().token }
// 상세: aidlc-docs/construction/unit4-table-session/frontend-integration-spec.md §2.1

/** 개발용 stopgap 토큰 저장 키. Unit 3 연결 시 제거 대상. */
export const ADMIN_TOKEN_KEY = 'admin_token'

/** 현재 관리자 JWT 를 반환. 없으면 null. */
export function getAdminToken(): string | null {
  try {
    return localStorage.getItem(ADMIN_TOKEN_KEY)
  } catch {
    return null
  }
}
