import { createApp, h } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory, RouterView } from 'vue-router'
import './style.css'
import App from './App.vue'

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: App,
      props: { city: 'sz' }
    },
    {
      path: '/sh',
      component: App,
      props: { city: 'sh' }
    },
    {
      path: '/bj',
      component: App,
      props: { city: 'bj' }
    },
    {
      path: '/gz',
      component: App,
      props: { city: 'gz' }
    },
    {
      path: '/wh',
      component: App,
      props: { city: 'wh' }
    },
    {
      path: '/cs',
      component: App,
      props: { city: 'cs' }
    },
    // Redirect /sz to / for consistency
    {
      path: '/sz',
      redirect: '/'
    }
  ]
})

// Create root component that renders router-view
const RootComponent = {
  render() {
    return h(RouterView)
  }
}

const app = createApp(RootComponent)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')
