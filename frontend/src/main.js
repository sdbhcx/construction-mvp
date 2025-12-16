import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'

const app = createApp(App)

// 配置Axios全局默认值
axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.timeout = 10000

// 挂载到Vue实例
app.config.globalProperties.$axios = axios

app.use(ElementPlus)
app.mount('#app')
