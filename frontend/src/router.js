import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('./views/LoginView.vue') },
    { path: '/', name: 'passenger', component: () => import('./views/PassengerView.vue'), meta: { requiresAuth: true, roles: ['PASSENGER'] } },
    { path: '/staff', name: 'staff', component: () => import('./views/StaffView.vue'), meta: { requiresAuth: true, roles: ['STAFF', 'ADMIN'] } },
    { path: '/admin', name: 'admin', component: () => import('./views/AdminView.vue'), meta: { requiresAuth: true, roles: ['ADMIN'] } },
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
