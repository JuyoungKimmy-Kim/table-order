<script setup lang="ts">
// Unit 4: 테이블 태블릿 초기 설정 (요구 3.2.3-1, §3.3.1)
// 번호 + 비밀번호 입력 → POST /api/admin/tables. 성공/실패 피드백.
import { ref } from 'vue'
import { createTable } from './api'
import { ApiError } from './http'

const tableNumber = ref<number | null>(null)
const password = ref('')
const submitting = ref(false)
const feedback = ref<{ kind: 'success' | 'error'; message: string } | null>(null)

async function submit() {
  feedback.value = null
  if (tableNumber.value === null || password.value.trim() === '') {
    feedback.value = { kind: 'error', message: '테이블 번호와 비밀번호를 모두 입력하세요.' }
    return
  }
  submitting.value = true
  try {
    const res = await createTable({ table_number: tableNumber.value, password: password.value })
    feedback.value = { kind: 'success', message: `테이블 ${res.table_number}번이 등록되었습니다. (자동 로그인 활성화)` }
    tableNumber.value = null
    password.value = ''
  } catch (e) {
    // §0.2 표준 에러 메시지 노출. CONFLICT=중복 번호, VALIDATION_ERROR=입력 오류
    const msg = e instanceof ApiError ? e.message : '등록 중 오류가 발생했습니다.'
    feedback.value = { kind: 'error', message: msg }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="table-setup">
    <h2>테이블 초기 설정</h2>
    <form @submit.prevent="submit">
      <label>
        테이블 번호
        <input v-model.number="tableNumber" type="number" min="1" required />
      </label>
      <label>
        테이블 비밀번호
        <input v-model="password" type="password" required autocomplete="new-password" />
      </label>
      <button type="submit" :disabled="submitting">{{ submitting ? '등록 중…' : '등록' }}</button>
    </form>
    <p v-if="feedback" :class="['feedback', feedback.kind]">{{ feedback.message }}</p>
    <p class="hint">16시간 세션은 등록된 자격으로 로그인 시 활성화됩니다. 실제 세션은 첫 주문 시 생성됩니다.</p>
  </section>
</template>

<style scoped>
.table-setup { max-width: 420px; }
form { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
button { padding: 10px; border: none; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.feedback { margin-top: 12px; padding: 10px; border-radius: 6px; }
.feedback.success { background: #ecfdf5; color: #065f46; }
.feedback.error { background: #fef2f2; color: #991b1b; }
.hint { margin-top: 16px; font-size: 12px; color: #6b7280; }
</style>
