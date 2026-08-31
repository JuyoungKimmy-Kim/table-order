<script setup>
// Unit 5: 메뉴 등록/수정 폼 모달 (§3.4.2 / §3.4.3).
// - PUT 은 전체 교체(결정 #2)이므로 수정 시에도 모든 필드를 제출한다.
// - 클라이언트 1차 검증(BR-9.1) + 서버 400 VALIDATION_ERROR details 를 필드에 매핑.
import { reactive, ref, watch, computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] }, // [{id, name}]
  menu: { type: Object, default: null }, // 수정 대상(없으면 등록)
})
const emit = defineEmits(['submit', 'cancel'])

const isEdit = computed(() => !!props.menu)

const form = reactive({
  category_id: null,
  name: '',
  price: 0,
  description: '',
  image_url: '',
  display_order: 0,
  is_available: true,
})
const errors = reactive({})

function resetFromProps() {
  const m = props.menu
  form.category_id = m ? m.category_id : (props.categories[0]?.id ?? null)
  form.name = m ? m.name : ''
  form.price = m ? m.price : 0
  form.description = m ? (m.description ?? '') : ''
  form.image_url = m ? (m.image_url ?? '') : ''
  form.display_order = m ? m.display_order : 0
  form.is_available = m ? m.is_available : true
  for (const k of Object.keys(errors)) delete errors[k]
}

watch(() => props.open, (v) => { if (v) resetFromProps() })

function validate() {
  for (const k of Object.keys(errors)) delete errors[k]
  if (!form.name || !form.name.trim()) errors.name = '메뉴명은 필수입니다.'
  if (!Number.isInteger(Number(form.price)) || Number(form.price) < 0) {
    errors.price = '가격은 0 이상의 정수여야 합니다.'
  }
  if (form.category_id == null) errors.category_id = '카테고리를 선택하세요.'
  return Object.keys(errors).length === 0
}

// 서버 400 details 를 필드 에러로 표시 (부모가 호출)
function applyServerErrors(details) {
  for (const k of Object.keys(errors)) delete errors[k]
  if (details && typeof details === 'object') {
    for (const [field, msg] of Object.entries(details)) errors[field] = msg
  }
}
defineExpose({ applyServerErrors })

function onSubmit() {
  if (!validate()) return
  emit('submit', {
    category_id: Number(form.category_id),
    name: form.name.trim(),
    price: Number(form.price),
    description: form.description || null,
    image_url: form.image_url || null,
    display_order: Number(form.display_order) || 0,
    is_available: !!form.is_available,
  })
}
</script>

<template>
  <div v-if="open" class="mf-backdrop" @click.self="emit('cancel')">
    <div class="mf-dialog" role="dialog" aria-modal="true">
      <h3 class="mf-title">{{ isEdit ? '메뉴 수정' : '메뉴 등록' }}</h3>

      <form class="mf-form" @submit.prevent="onSubmit">
        <label class="mf-field">
          <span>카테고리</span>
          <select v-model="form.category_id">
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <small v-if="errors.category_id" class="mf-err">{{ errors.category_id }}</small>
        </label>

        <label class="mf-field">
          <span>메뉴명 *</span>
          <input v-model="form.name" type="text" maxlength="100" />
          <small v-if="errors.name" class="mf-err">{{ errors.name }}</small>
        </label>

        <label class="mf-field">
          <span>가격(원) *</span>
          <input v-model.number="form.price" type="number" min="0" step="1" />
          <small v-if="errors.price" class="mf-err">{{ errors.price }}</small>
        </label>

        <label class="mf-field">
          <span>설명</span>
          <textarea v-model="form.description" rows="2"></textarea>
        </label>

        <label class="mf-field">
          <span>이미지 URL</span>
          <input v-model="form.image_url" type="text" placeholder="https://..." />
        </label>

        <div class="mf-row">
          <label class="mf-field mf-field--sm">
            <span>노출 순서</span>
            <input v-model.number="form.display_order" type="number" step="1" />
          </label>
          <label class="mf-check">
            <input v-model="form.is_available" type="checkbox" />
            <span>노출(주문 가능)</span>
          </label>
        </div>

        <div class="mf-actions">
          <button type="button" class="mf-btn" @click="emit('cancel')">취소</button>
          <button type="submit" class="mf-btn mf-btn--primary">
            {{ isEdit ? '저장' : '등록' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.mf-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.mf-dialog {
  background: #fff; border-radius: 10px; padding: 24px; width: min(520px, 94vw);
  max-height: 90vh; overflow: auto; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
.mf-title { margin: 0 0 16px; font-size: 18px; }
.mf-form { display: flex; flex-direction: column; gap: 12px; }
.mf-field { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
.mf-field span { color: #333; font-weight: 500; }
.mf-field input, .mf-field select, .mf-field textarea {
  padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px;
}
.mf-row { display: flex; gap: 16px; align-items: flex-end; }
.mf-field--sm { max-width: 140px; }
.mf-check { display: flex; align-items: center; gap: 6px; font-size: 14px; }
.mf-err { color: #e5484d; font-size: 12px; }
.mf-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.mf-btn {
  padding: 8px 16px; border-radius: 6px; border: 1px solid #ccc;
  background: #f5f5f5; cursor: pointer; font-size: 14px;
}
.mf-btn--primary { background: #0b74de; border-color: #0b74de; color: #fff; }
</style>
