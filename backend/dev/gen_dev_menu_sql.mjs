/**
 * 개발용 메뉴 시드 SQL 생성기.
 *
 * frontend/customer/src/mock/restaurant-menu.js 를 읽어
 * dev/dev_menu_reset.sql 을 생성한다.
 *
 * ⚠️ 이 SQL 은 migrations 디렉토리 밖(dev/)에 둔다.
 *    db.apply_migrations() 는 migrations/*.sql 만 스캔하므로, 여기 두면
 *    일반(프로덕션) 서버 시작 시 절대 자동 실행되지 않는다. 개발 초기화는
 *    dev/dev_reset.py 로만 명시적으로 실행한다.
 *
 * 이 SQL 은 "메뉴/카테고리만" 초기화한다:
 *   - STORE001 매장의 categories/menus 를 모두 지우고 mock 데이터로 재삽입.
 *   - stores/admin/tables/sessions/orders/guestbook 등은 건드리지 않는다.
 *   - order_items 가 menus 를 FK 참조하므로, 실행 스크립트에서 PRAGMA foreign_keys=OFF
 *     로 감싼다(스냅샷 원칙상 주문 항목은 menu_name/unit_price 를 자체 보관 — §1.8).
 *
 * 실행: node dev/gen_dev_menu_sql.mjs   (backend 디렉토리에서)
 */
import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const MOCK = resolve(__dirname, '../../frontend/customer/src/mock/restaurant-menu.js')
const OUT = resolve(__dirname, 'dev_menu_reset.sql')

const { restaurantMenu } = await import(MOCK)

// SQL 문자열 리터럴 이스케이프 (작은따옴표 2배). NULL 은 그대로.
const s = (v) => (v == null ? 'NULL' : `'${String(v).replace(/'/g, "''")}'`)
const n = (v) => (v == null ? 'NULL' : String(Number(v)))

const lines = []
lines.push('-- ⚠️ 자동 생성 파일 — 직접 수정하지 말 것.')
lines.push('-- 원본: frontend/customer/src/mock/restaurant-menu.js')
lines.push('-- 생성기: dev/gen_dev_menu_sql.mjs')
lines.push('-- 용도: 개발 서버 시작 시 STORE001 의 메뉴/카테고리만 mock 데이터로 초기화.')
lines.push('--')
lines.push('-- 주의: order_items 의 menu_id FK 때문에, 실행측(dev_reset)에서')
lines.push('--       PRAGMA foreign_keys=OFF 로 감싸 실행한다.')
lines.push('')
lines.push("-- STORE001 이 없으면 아무 것도 하지 않도록, 실행측에서 존재 보장(seed) 후 호출한다.")
lines.push('')
lines.push('-- 1) 기존 메뉴/카테고리 제거 (해당 매장 한정)')
lines.push("DELETE FROM menus      WHERE store_id = (SELECT id FROM stores WHERE store_code = 'STORE001');")
lines.push("DELETE FROM categories WHERE store_id = (SELECT id FROM stores WHERE store_code = 'STORE001');")
lines.push('')

const NOW = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"
const STORE = "(SELECT id FROM stores WHERE store_code = 'STORE001')"

lines.push('-- 2) 카테고리 삽입')
for (const cat of restaurantMenu.categories) {
  lines.push(
    `INSERT INTO categories(store_id, name, display_order, created_at, updated_at) ` +
    `VALUES (${STORE}, ${s(cat.name)}, ${n(cat.display_order)}, ${NOW}, ${NOW});`
  )
}
lines.push('')

lines.push('-- 3) 메뉴 삽입 (category_id 는 방금 삽입한 카테고리를 name 으로 참조)')
for (const cat of restaurantMenu.categories) {
  const catRef =
    `(SELECT id FROM categories WHERE store_id = ${STORE} AND name = ${s(cat.name)})`
  for (const m of cat.menus) {
    lines.push(
      `INSERT INTO menus(store_id, category_id, name, price, description, image_url, ` +
      `display_order, is_available, created_at, updated_at) VALUES (` +
      `${STORE}, ${catRef}, ${s(m.name)}, ${n(m.price)}, ${s(m.description)}, ` +
      `${s(m.image_url)}, ${n(m.display_order)}, ${m.is_available ? 1 : 0}, ${NOW}, ${NOW});`
    )
  }
}
lines.push('')

const catCount = restaurantMenu.categories.length
const menuCount = restaurantMenu.categories.reduce((a, c) => a + c.menus.length, 0)
lines.push(`-- 완료: 카테고리 ${catCount}개, 메뉴 ${menuCount}개`)
lines.push('')

writeFileSync(OUT, lines.join('\n'), 'utf-8')
console.log(`생성 완료: ${OUT}`)
console.log(`  카테고리 ${catCount}개, 메뉴 ${menuCount}개`)
