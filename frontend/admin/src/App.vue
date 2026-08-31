<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app">
    <header v-if="auth.isAuthenticated" class="topbar">
      <span class="brand">테이블오더 관리자</span>
      <span class="user">{{ auth.username }}</span>
      <button @click="logout">로그아웃</button>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; background: #f4f5f7; color: #222; }
.topbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px;
  background: #1f2937; color: #fff; }
.topbar .brand { font-weight: 700; }
.topbar .user { margin-left: auto; }
.topbar button { padding: 4px 10px; }
main { padding: 16px; }
</style>
