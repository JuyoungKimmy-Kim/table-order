<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'

// 초기 설정/로그인 (3.1.1, frontend-components.md §4.1).
const session = useSessionStore()
const router = useRouter()

const storeCode = ref('STORE001')
const tableNumber = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  if (!storeCode.value || !tableNumber.value || !password.value) {
    error.value = '모든 항목을 입력하세요.'
    return
  }
  submitting.value = true
  try {
    await session.login(storeCode.value, tableNumber.value, password.value)
    router.push({ name: 'menu' })
  } catch (e) {
    error.value = e.status === 401 ? '로그인 정보를 확인하세요.' : (e.message || '로그인에 실패했습니다.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="setup" data-testid="setup-view">
    <h1 class="brand">🍽️ 테이블 주문</h1>
    <form class="card-form" @submit.prevent="submit">
      <label>매장 코드
        <input v-model="storeCode" data-testid="input-store-code" autocomplete="off" />
      </label>
      <label>테이블 번호
        <input v-model="tableNumber" type="number" inputmode="numeric" data-testid="input-table-number" />
      </label>
      <label>비밀번호
        <input v-model="password" type="password" data-testid="input-password" />
      </label>
      <p v-if="error" class="error" data-testid="login-error">{{ error }}</p>
      <button class="primary" type="submit" :disabled="submitting" data-testid="btn-login">
        {{ submitting ? '입장 중…' : '입장하기' }}
      </button>
    </form>
  </div>
</template>
