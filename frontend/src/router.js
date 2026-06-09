import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'
import LoginView from './views/LoginView.vue'
import PassengerView from './views/PassengerView.vue'
import StaffView from './views/StaffView.vue'
import AdminView from './views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'passenger', component: PassengerView, meta: { requiresAuth: true, roles: ['PASSENGER'] } },
    { path: '/staff', name: 'staff', component: StaffView, meta: { requiresAuth: true, roles: ['STAFF', 'ADMIN'] } },
    { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAuth: true, roles: ['ADMIN'] } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (auth.user === null) {
    await auth.fetchMe()
  }
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    return auth.role === 'ADMIN' ? '/admin' : auth.role === 'STAFF' ? '/staff' : '/'
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return auth.role === 'ADMIN' ? '/admin' : auth.role === 'STAFF' ? '/staff' : '/'
  }
})

export default router
