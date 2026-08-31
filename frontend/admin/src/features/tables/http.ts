// Unit 4: 경량 HTTP 클라이언트 (임시 shim)
//
// CONTRACT-GAP: 계약은 base `/api`(§0.1)·에러 envelope(§0.2)·인증 헤더(§0.3)만 정의하고,
// 프론트 공유 HTTP 클라이언트(공통 axios 인스턴스/인터셉터)는 정의하지 않는다.
//
// INTEGRATION-TODO(admin-scaffold): 공유 admin 골격에 공통 HTTP 클라이언트가 생기면
// 이 파일을 그것으로 대체하고 api.ts 의 import 만 교체한다. 교체 비용을 줄이기 위해
// request(method, path, opts) 시그니처를 단순하게 유지한다.
// 상세: aidlc-docs/construction/unit4-table-session/frontend-integration-spec.md §2.2

import { getAdminToken } from './auth-bridge'

const BASE_URL = '/api' // §0.1

/** 계약 §0.2 에러 envelope 를 표현하는 예외. */
export class ApiError extends Error {
  code: string
  status: number
  details: Record<string, unknown>
  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

interface RequestOpts {
  body?: unknown
  query?: Record<string, string | number | undefined>
}

function buildUrl(path: string, query?: RequestOpts['query']): string {
  const url = new URL(BASE_URL + path, window.location.origin)
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v))
    }
  }
  return url.pathname + url.search
}

export async function request<T>(method: string, path: string, opts: RequestOpts = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json; charset=utf-8' }

  // §0.3 관리자 인증 헤더 주입. 토큰 소스는 auth-bridge(CONTRACT-GAP).
  const token = getAdminToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(buildUrl(path, opts.query), {
    method,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  if (res.status === 204) return undefined as T

  const text = await res.text()
  const data = text ? JSON.parse(text) : undefined

  if (!res.ok) {
    // §0.2: { "error": { code, message, details } }
    const err = data?.error ?? {}
    throw new ApiError(res.status, err.code ?? 'INTERNAL_ERROR', err.message ?? '요청 처리 중 오류가 발생했습니다.', err.details ?? {})
  }
  return data as T
}
