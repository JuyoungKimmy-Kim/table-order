<script setup>
// Unit 5: 메뉴 관리 메인 화면 (§3.2.4 / 계약 §3.4).
// 기능: 카테고리별 메뉴 목록, 등록/수정/삭제, 노출 순서 조정(위/아래), 가용성 표시.
// 삭제는 확인 팝업 후 실행하며, 참조 주문이 있으면 409(MENU_IN_USE)를 안내한다(결정 #1).
import { ref, reactive, onMounted } from 'vue'
import { menuApi, ApiError } from '../api/menuApi.js'
import MenuFormModal from '../components/MenuFormModal.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const loading = ref(false)
const banner = reactive({ text: '', kind: 'info' }) // kind: info|error|success
const categories = ref([]) // [{id, name, display_order, menus:[...]}]
const flatCategories = ref([]) // [{id, name}] 폼 셀렉트용

const formOpen = ref(false)
const editingMenu = ref(null)
const formRef = ref(null)

const confirm = reactive({ open: false, menu: null })

function setBanner(text, kind = 'info') {
  banner.text = text
  banner.kind = kind
}
function clearBanner() { banner.text = '' }

async function load() {
  loading.value = true
  clearBanner()
  try {
    const data = await menuApi.listMenus()
    categories.value = data.categories || []
    flatCategories.value = categories.value.map((c) => ({ id: c.id, name: c.name }))
  } catch (e) {
    handleError(e, '메뉴를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

function handleError(e, fallback) {
  if (e instanceof ApiError) {
    if (e.status === 401) return setBanner('세션이 만료되었습니다. 다시 로그인하세요.', 'error')
    return setBanner(e.message || fallback, 'error')
  }
  setBanner(fallback, 'error')
}

// --- 등록/수정 ---
function openCreate() {
  editingMenu.value = null
  formOpen.value = true
}
function openEdit(menu) {
  editingMenu.value = { ...menu }
  formOpen.value = true
}
async function onFormSubmit(payload) {
  try {
    if (editingMenu.value) {
      await menuApi.updateMenu(editingMenu.value.id, payload)
      setBanner('메뉴를 수정했습니다.', 'success')
    } else {
      await menuApi.createMenu(payload)
      setBanner('메뉴를 등록했습니다.', 'success')
    }
    formOpen.value = false
    await load()
  } catch (e) {
    // 서버 검증 오류는 폼 필드에 매핑
    if (e instanceof ApiError && e.code === 'VALIDATION_ERROR') {
      formRef.value?.applyServerErrors(e.details)
    } else {
      formOpen.value = false
      handleError(e, '저장에 실패했습니다.')
    }
  }
}

// --- 삭제 ---
function askDelete(menu) {
  confirm.menu = menu
  confirm.open = true
}
async function onConfirmDelete() {
  const menu = confirm.menu
  confirm.open = false
  try {
    await menuApi.deleteMenu(menu.id)
    setBanner(`'${menu.name}' 메뉴를 삭제했습니다.`, 'success')
    await load()
  } catch (e) {
    if (e instanceof ApiError && e.code === 'MENU_IN_USE') {
      setBanner(
        `'${menu.name}'은(는) 주문 내역이 있어 삭제할 수 없습니다. 대신 '노출 끄기'로 숨기세요.`,
        'error',
      )
    } else {
      handleError(e, '삭제에 실패했습니다.')
    }
  }
}

// --- 노출 순서 조정 (§3.4.5) ---
async function move(category, index, dir) {
  const menus = category.menus
  const target = index + dir
  if (target < 0 || target >= menus.length) return
  const a = menus[index]
  const b = menus[target]
  try {
    await menuApi.reorderMenus([
      { menu_id: a.id, display_order: b.display_order },
      { menu_id: b.id, display_order: a.display_order },
    ])
    await load()
  } catch (e) {
    handleError(e, '순서 변경에 실패했습니다.')
  }
}

function formatPrice(n) {
  return `${Number(n).toLocaleString('ko-KR')}원`
}

onMounted(load)
</script>

<template>
  <section class="menu-view">
    <header class="menu-view__head">
      <h2>메뉴 관리</h2>
      <div class="menu-view__actions">
        <button class="btn" @click="load" :disabled="loading">새로고침</button>
        <button class="btn btn--primary" @click="openCreate">+ 메뉴 등록</button>
      </div>
    </header>

    <p v-if="banner.text" class="banner" :class="`banner--${banner.kind}`">{{ banner.text }}</p>

    <p v-if="loading" class="muted">불러오는 중…</p>
    <p v-else-if="categories.length === 0" class="muted">등록된 카테고리가 없습니다.</p>

    <div v-for="cat in categories" :key="cat.id" class="cat">
      <h3 class="cat__name">{{ cat.name }}</h3>
      <p v-if="cat.menus.length === 0" class="muted">메뉴가 없습니다.</p>
      <table v-else class="tbl">
        <thead>
          <tr>
            <th>순서</th><th>메뉴명</th><th>가격</th><th>노출</th><th class="tbl__act">관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(m, i) in cat.menus" :key="m.id" :class="{ 'row--hidden': !m.is_available }">
            <td class="tbl__order">
              <button class="mini" :disabled="i === 0" @click="move(cat, i, -1)" aria-label="위로">▲</button>
              <button class="mini" :disabled="i === cat.menus.length - 1" @click="move(cat, i, 1)" aria-label="아래로">▼</button>
            </td>
            <td>{{ m.name }}</td>
            <td>{{ formatPrice(m.price) }}</td>
            <td>
              <span class="tag" :class="m.is_available ? 'tag--on' : 'tag--off'">
                {{ m.is_available ? '노출' : '숨김' }}
              </span>
            </td>
            <td class="tbl__act">
              <button class="btn" @click="openEdit(m)">수정</button>
              <button class="btn btn--danger" @click="askDelete(m)">삭제</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <MenuFormModal
      ref="formRef"
      :open="formOpen"
      :categories="flatCategories"
      :menu="editingMenu"
      @submit="onFormSubmit"
      @cancel="formOpen = false"
    />

    <ConfirmDialog
      :open="confirm.open"
      title="메뉴 삭제"
      :message="`'${confirm.menu?.name ?? ''}' 메뉴를 삭제하시겠습니까?\n주문 내역이 있는 메뉴는 삭제할 수 없습니다.`"
      confirm-label="삭제"
      @confirm="onConfirmDelete"
      @cancel="confirm.open = false"
    />
  </section>
</template>

<style scoped>
.menu-view { max-width: 900px; margin: 0 auto; padding: 16px; }
.menu-view__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.menu-view__actions { display: flex; gap: 8px; }
.cat { margin-bottom: 24px; }
.cat__name { font-size: 16px; margin: 0 0 8px; padding-bottom: 4px; border-bottom: 2px solid #eee; }
.tbl { width: 100%; border-collapse: collapse; font-size: 14px; }
.tbl th, .tbl td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }
.tbl__act { text-align: right; white-space: nowrap; }
.tbl__order { white-space: nowrap; }
.row--hidden td { color: #999; }
.tag { padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.tag--on { background: #e6f4ea; color: #1e7e34; }
.tag--off { background: #f1f1f1; color: #777; }
.btn { padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px; background: #f7f7f7; cursor: pointer; font-size: 13px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--primary { background: #0b74de; border-color: #0b74de; color: #fff; }
.btn--danger { background: #fff; border-color: #e5484d; color: #e5484d; }
.mini { width: 26px; padding: 2px 0; border: 1px solid #ddd; background: #fafafa; cursor: pointer; border-radius: 4px; }
.mini:disabled { opacity: 0.35; cursor: not-allowed; }
.muted { color: #888; font-size: 14px; }
.banner { padding: 10px 14px; border-radius: 6px; font-size: 14px; margin: 8px 0 16px; }
.banner--info { background: #eef4fb; color: #23496e; }
.banner--error { background: #fdecec; color: #a12026; }
.banner--success { background: #e6f4ea; color: #1e7e34; }
</style>
