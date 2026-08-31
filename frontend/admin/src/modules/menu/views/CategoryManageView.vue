<script setup>
// Unit 5: 카테고리 관리 화면 (§3.4.6).
// 등록/수정/삭제 + 노출 순서(display_order). 하위 메뉴가 있는 카테고리 삭제 시
// 409(CATEGORY_IN_USE)를 안내한다(결정 #3).
import { ref, reactive, onMounted } from 'vue'
import { menuApi, ApiError } from '../api/menuApi.js'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const loading = ref(false)
const banner = reactive({ text: '', kind: 'info' })
const categories = ref([])

const draft = reactive({ id: null, name: '', display_order: 0 })
const nameErr = ref('')
const confirm = reactive({ open: false, category: null })

function setBanner(text, kind = 'info') { banner.text = text; banner.kind = kind }

async function load() {
  loading.value = true
  banner.text = ''
  try {
    const data = await menuApi.listCategories()
    categories.value = data.categories || []
  } catch (e) {
    handleError(e, '카테고리를 불러오지 못했습니다.')
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

function resetDraft() { draft.id = null; draft.name = ''; draft.display_order = 0; nameErr.value = '' }
function editCategory(c) { draft.id = c.id; draft.name = c.name; draft.display_order = c.display_order; nameErr.value = '' }

async function save() {
  nameErr.value = ''
  if (!draft.name.trim()) { nameErr.value = '카테고리명은 필수입니다.'; return }
  const payload = { name: draft.name.trim(), display_order: Number(draft.display_order) || 0 }
  try {
    if (draft.id) {
      await menuApi.updateCategory(draft.id, payload)
      setBanner('카테고리를 수정했습니다.', 'success')
    } else {
      await menuApi.createCategory(payload)
      setBanner('카테고리를 등록했습니다.', 'success')
    }
    resetDraft()
    await load()
  } catch (e) {
    if (e instanceof ApiError && e.code === 'VALIDATION_ERROR') {
      nameErr.value = e.details?.name || e.message
    } else {
      handleError(e, '저장에 실패했습니다.')
    }
  }
}

function askDelete(c) { confirm.category = c; confirm.open = true }
async function onConfirmDelete() {
  const c = confirm.category
  confirm.open = false
  try {
    await menuApi.deleteCategory(c.id)
    setBanner(`'${c.name}' 카테고리를 삭제했습니다.`, 'success')
    if (draft.id === c.id) resetDraft()
    await load()
  } catch (e) {
    if (e instanceof ApiError && e.code === 'CATEGORY_IN_USE') {
      setBanner(`'${c.name}'에 메뉴가 남아 있어 삭제할 수 없습니다. 메뉴를 먼저 이동/삭제하세요.`, 'error')
    } else {
      handleError(e, '삭제에 실패했습니다.')
    }
  }
}

onMounted(load)
</script>

<template>
  <section class="cat-view">
    <header class="cat-view__head"><h2>카테고리 관리</h2></header>

    <p v-if="banner.text" class="banner" :class="`banner--${banner.kind}`">{{ banner.text }}</p>

    <div class="editor">
      <input v-model="draft.name" type="text" placeholder="카테고리명" maxlength="50" />
      <input v-model.number="draft.display_order" type="number" step="1" class="editor__order" placeholder="순서" />
      <button class="btn btn--primary" @click="save">{{ draft.id ? '저장' : '등록' }}</button>
      <button v-if="draft.id" class="btn" @click="resetDraft">취소</button>
    </div>
    <small v-if="nameErr" class="err">{{ nameErr }}</small>

    <p v-if="loading" class="muted">불러오는 중…</p>
    <ul v-else class="list">
      <li v-for="c in categories" :key="c.id" class="list__item">
        <span class="list__order">#{{ c.display_order }}</span>
        <span class="list__name">{{ c.name }}</span>
        <span class="list__act">
          <button class="btn" @click="editCategory(c)">수정</button>
          <button class="btn btn--danger" @click="askDelete(c)">삭제</button>
        </span>
      </li>
    </ul>

    <ConfirmDialog
      :open="confirm.open"
      title="카테고리 삭제"
      :message="`'${confirm.category?.name ?? ''}' 카테고리를 삭제하시겠습니까?\n메뉴가 남아 있으면 삭제할 수 없습니다.`"
      confirm-label="삭제"
      @confirm="onConfirmDelete"
      @cancel="confirm.open = false"
    />
  </section>
</template>

<style scoped>
.cat-view { max-width: 720px; margin: 0 auto; padding: 16px; }
.cat-view__head h2 { margin: 0 0 12px; }
.editor { display: flex; gap: 8px; align-items: center; }
.editor input { padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
.editor__order { max-width: 90px; }
.err { color: #e5484d; font-size: 12px; display: block; margin-top: 4px; }
.list { list-style: none; padding: 0; margin: 16px 0 0; }
.list__item { display: flex; align-items: center; gap: 12px; padding: 10px 6px; border-bottom: 1px solid #f0f0f0; }
.list__order { color: #999; font-size: 13px; min-width: 40px; }
.list__name { flex: 1; }
.list__act { display: flex; gap: 6px; }
.btn { padding: 6px 12px; border: 1px solid #ccc; border-radius: 6px; background: #f7f7f7; cursor: pointer; font-size: 13px; }
.btn--primary { background: #0b74de; border-color: #0b74de; color: #fff; }
.btn--danger { background: #fff; border-color: #e5484d; color: #e5484d; }
.muted { color: #888; font-size: 14px; }
.banner { padding: 10px 14px; border-radius: 6px; font-size: 14px; margin: 8px 0 16px; }
.banner--info { background: #eef4fb; color: #23496e; }
.banner--error { background: #fdecec; color: #a12026; }
.banner--success { background: #e6f4ea; color: #1e7e34; }
</style>
