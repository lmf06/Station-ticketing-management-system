<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { House, Tickets, SwitchButton, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

const roleName = computed(() => {
  if (auth.role === 'ADMIN') return '管理员'
  if (auth.role === 'STAFF') return '售票员'
  if (auth.role === 'PASSENGER') return '旅客'
  return '未登录'
})

async function logout() {
  await auth.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside v-if="auth.isAuthenticated" class="side-nav">
      <div class="brand">
        <span class="brand-mark">票</span>
        <div>
          <strong>车站售票管理系统</strong>
          <small>汽车客运站</small>
        </div>
      </div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/">
          <el-icon><Tickets /></el-icon>
          <span>旅客购票</span>
        </el-menu-item>
        <el-menu-item v-if="['STAFF', 'ADMIN'].includes(auth.role)" index="/staff">
          <el-icon><House /></el-icon>
          <span>窗口业务</span>
        </el-menu-item>
        <el-menu-item v-if="auth.role === 'ADMIN'" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <main class="main-area">
      <header v-if="auth.isAuthenticated" class="top-bar">
        <div>
          <h1>{{ $route.name === 'admin' ? '系统管理' : $route.name === 'staff' ? '窗口业务' : '旅客购票' }}</h1>
          <p>{{ roleName }}：{{ auth.user?.displayName }}</p>
        </div>
        <el-button :icon="SwitchButton" @click="logout">退出</el-button>
      </header>
      <router-view />
    </main>
  </div>
</template>
