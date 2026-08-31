<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const storeCode = ref('STORE001')
const username = ref('')
const password = ref('')
const submitting = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!storeCode.value || !username.value || !password.value) {
    error.value = '모든 항목을 입력하세요.'
    return
  }
  submitting.value = true
  try {
    await auth.login(storeCode.value, username.value, password.value)
    router.push(route.query.redirect || '/')
  } catch (e) {
    if (e.status === 429) error.value = '로그인 시도가 많습니다. 5분 후 다시 시도하세요.'
    else if (e.status === 401) error.value = '아이디 또는 비밀번호가 올바르지 않습니다.'
    else error.value = '로그인 중 오류가 발생했습니다.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <h1>관리자 로그인</h1>
      <label>매장 코드<input v-model="storeCode" autocomplete="off" /></label>
      <label>아이디<input v-model="username" autocomplete="username" /></label>
      <label>비밀번호<input v-model="password" type="password" autocomplete="current-password" /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="submitting">{{ submitting ? '로그인 중…' : '로그인' }}</button>
    </form>
  </div>
</template>

<style scoped>
.login-wrap { display: flex; justify-content: center; padding-top: 8vh; }
.login-card { display: flex; flex-direction: column; gap: 12px; width: 320px;
  background: #fff; padding: 24px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.login-card h1 { font-size: 20px; margin: 0 0 8px; }
.login-card label { display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.login-card input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
.login-card button { padding: 10px; background: #2563eb; color: #fff; border: 0; border-radius: 6px;
  cursor: pointer; }
.login-card button:disabled { opacity: .6; }
.error { color: #dc2626; font-size: 13px; margin: 0; }
</style>
