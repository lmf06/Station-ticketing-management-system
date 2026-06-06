<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, User, Phone, CreditCard, Right } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({
  username: 'admin',
  password: 'admin123',
})

const registerForm = reactive({
  username: '',
  password: '',
  displayName: '',
  idCard: '',
  phone: '',
})

async function afterAuth() {
  if (auth.role === 'ADMIN') await router.push('/admin')
  else if (auth.role === 'STAFF') await router.push('/staff')
  else await router.push('/')
}

async function submitLogin() {
  loading.value = true
  try {
    await auth.login(loginForm)
    ElMessage.success('登录成功')
    await afterAuth()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function submitRegister() {
  loading.value = true
  try {
    await auth.register(registerForm)
    ElMessage.success('注册成功')
    await afterAuth()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function fillDemo(role) {
  if (role === 'admin') Object.assign(loginForm, { username: 'admin', password: 'admin123' })
  if (role === 'staff') Object.assign(loginForm, { username: 'staff', password: 'staff123' })
  if (role === 'passenger') Object.assign(loginForm, { username: 'passenger', password: 'passenger123' })
}
</script>

<template>
  <section class="login-page">
    <div class="login-form">
      <h1>车站售票管理系统</h1>
      <p>2025/2026 数据库课程设计</p>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form label-position="top" @submit.prevent="submitLogin">
            <el-form-item label="账号">
              <el-input v-model="loginForm.username" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" :prefix-icon="Lock" type="password" show-password />
            </el-form-item>
            <div class="table-actions" style="margin-bottom: 16px">
              <el-button size="small" @click="fillDemo('admin')">管理员</el-button>
              <el-button size="small" @click="fillDemo('staff')">售票员</el-button>
              <el-button size="small" @click="fillDemo('passenger')">旅客</el-button>
            </div>
            <el-button type="primary" :icon="Right" :loading="loading" style="width: 100%" @click="submitLogin">登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="旅客注册" name="register">
          <el-form label-position="top" @submit.prevent="submitRegister">
            <el-form-item label="账号">
              <el-input v-model="registerForm.username" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" :prefix-icon="Lock" type="password" show-password />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="registerForm.displayName" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="证件号">
              <el-input v-model="registerForm.idCard" :prefix-icon="CreditCard" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="registerForm.phone" :prefix-icon="Phone" />
            </el-form-item>
            <el-button type="primary" :icon="Right" :loading="loading" style="width: 100%" @click="submitRegister">注册并登录</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
    <div class="login-side">
      <h2>杭州汽车客运中心 08:30 班次</h2>
    </div>
  </section>
</template>
