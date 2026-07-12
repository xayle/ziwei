import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router, { registerRouterGuards } from './router'
import './assets/variables.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
registerRouterGuards(router)
app.mount('#app')
