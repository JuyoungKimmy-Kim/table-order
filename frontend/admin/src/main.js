import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())

// 부팅 시 localStorage 토큰 복원(새로고침 세션 유지, 3.2.1)
const auth = useAuthStore()
auth.loadFromStorage()

app.use(router)
app.mount('#app')
