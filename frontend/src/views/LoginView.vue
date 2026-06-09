<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, User, Phone, CreditCard } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const flipped = ref(false)
const loading = ref(false)
const welcomeMsg = ref('')
const transitioning = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  password: '',
  displayName: '',
  idCard: '',
  phone: '',
})

const loginErrors = reactive({ username: '', password: '', form: '' })
const registerErrors = reactive({ username: '', password: '', displayName: '', idCard: '', phone: '', form: '' })

function clearLoginErrors() {
  loginErrors.username = ''
  loginErrors.password = ''
  loginErrors.form = ''
}

function clearRegisterErrors() {
  registerErrors.username = ''
  registerErrors.password = ''
  registerErrors.displayName = ''
  registerErrors.idCard = ''
  registerErrors.phone = ''
  registerErrors.form = ''
}

const rules = {
  username(v) {
    if (!v) return '请输入账号'
    if (v.length < 2) return '账号至少 2 个字符'
    if (v.length > 64) return '账号不能超过 64 个字符'
    return ''
  },
  password(v) {
    if (!v) return '请输入密码'
    if (v.length < 6) return '密码长度不能少于 6 位'
    return ''
  },
  phone(v) {
    if (!v) return '请输入手机号'
    if (!/^1[3-9]\d{9}$/.test(v)) return '手机号格式不正确'
    return ''
  },
  idCard(v) {
    if (!v) return '请输入证件号'
    if (!/^\d{17}[\dXx]$/.test(v)) return '证件号格式不正确（18位）'
    return ''
  },
  displayName(v) {
    if (!v) return '请输入姓名'
    return ''
  },
}

function validateRegisterField(field) {
  const error = rules[field](registerForm[field].trim())
  registerErrors[field] = error
  return !error
}

function validateAll() {
  const fields = ['username', 'password', 'displayName', 'phone', 'idCard']
  let valid = true
  fields.forEach((f) => {
    if (!validateRegisterField(f)) valid = false
  })
  return valid
}

async function afterAuth() {
  transitioning.value = true
  welcomeMsg.value = `欢迎回来，${auth.user?.displayName || ''}`
  await new Promise((r) => setTimeout(r, 1200))
  if (auth.role === 'ADMIN') await router.push('/admin')
  else if (auth.role === 'STAFF') await router.push('/staff')
  else await router.push('/')
}

async function submitLogin() {
  clearLoginErrors()
  const u = loginForm.username.trim()
  if (!u) { loginErrors.username = '请输入账号'; return }
  if (!loginForm.password) { loginErrors.password = '请输入密码'; return }
  loading.value = true
  try {
    await auth.login({ username: u, password: loginForm.password })
    await afterAuth()
  } catch (error) {
    loginErrors.form = error.message
    loading.value = false
  }
}

async function submitRegister() {
  clearRegisterErrors()
  if (!validateAll()) return
  loading.value = true
  try {
    await auth.register(registerForm)
    await afterAuth()
  } catch (error) {
    registerErrors.form = error.message
    loading.value = false
  }
}

function toggleCard() {
  clearLoginErrors()
  clearRegisterErrors()
  flipped.value = !flipped.value
}
</script>

<template>
  <section class="login-page">
    <!-- Welcome transition overlay -->
    <Transition name="welcome-fade">
      <div v-if="transitioning" class="welcome-overlay">
        <div class="welcome-card">
          <div class="welcome-check">&#10003;</div>
          <h2>{{ welcomeMsg }}</h2>
          <p>正在跳转…</p>
        </div>
      </div>
    </Transition>

    <!-- Left: form panel -->
    <div class="login-form">
      <div class="form-brand">
        <span class="form-brand-mark">票</span>
        <div>
          <strong>车站售票管理系统</strong>
          <small>汽车客运站</small>
        </div>
      </div>

      <div class="card-scene">
        <Transition name="card-flip" mode="out-in">
          <!-- Login card -->
          <div v-if="!flipped" key="login" class="card-panel">
            <h3>账号登录</h3>
            <el-form label-position="top" @submit.prevent="submitLogin">
              <el-form-item label="账号" :error="loginErrors.username">
                <el-input
                  v-model="loginForm.username"
                  :prefix-icon="User"
                  placeholder="请输入账号"
                  @input="loginErrors.username = ''"
                />
              </el-form-item>
              <el-form-item label="密码" :error="loginErrors.password">
                <el-input
                  v-model="loginForm.password"
                  :prefix-icon="Lock"
                  type="password"
                  show-password
                  placeholder="请输入密码"
                  @input="loginErrors.password = ''"
                />
              </el-form-item>
              <p v-if="loginErrors.form" class="form-error">{{ loginErrors.form }}</p>
              <el-button type="primary" :loading="loading" style="width: 100%" @click="submitLogin">
                登录
              </el-button>
            </el-form>
            <p class="switch-link">
              还没有账号？<a href="javascript:void(0)" @click="toggleCard">立即注册</a>
            </p>
          </div>

          <!-- Register card -->
          <div v-else key="register" class="card-panel">
            <h3>旅客注册</h3>
            <el-form label-position="top" @submit.prevent="submitRegister">
              <el-form-item label="账号" :error="registerErrors.username">
                <el-input
                  v-model="registerForm.username"
                  :prefix-icon="User"
                  placeholder="2-64 个字符"
                  @input="validateRegisterField('username')"
                />
              </el-form-item>
              <el-form-item label="密码" :error="registerErrors.password">
                <el-input
                  v-model="registerForm.password"
                  :prefix-icon="Lock"
                  type="password"
                  show-password
                  placeholder="不少于 6 位"
                  @input="validateRegisterField('password')"
                />
              </el-form-item>
              <el-form-item label="姓名" :error="registerErrors.displayName">
                <el-input
                  v-model="registerForm.displayName"
                  :prefix-icon="User"
                  placeholder="请输入姓名"
                  @input="validateRegisterField('displayName')"
                />
              </el-form-item>
              <el-form-item label="证件号" :error="registerErrors.idCard">
                <el-input
                  v-model="registerForm.idCard"
                  :prefix-icon="CreditCard"
                  placeholder="18 位身份证号码"
                  @input="validateRegisterField('idCard')"
                />
              </el-form-item>
              <el-form-item label="手机号" :error="registerErrors.phone">
                <el-input
                  v-model="registerForm.phone"
                  :prefix-icon="Phone"
                  placeholder="11 位手机号码"
                  @input="validateRegisterField('phone')"
                />
              </el-form-item>
              <p v-if="registerErrors.form" class="form-error">{{ registerErrors.form }}</p>
              <el-button type="primary" :loading="loading" style="width: 100%" @click="submitRegister">
                注册并登录
              </el-button>
            </el-form>
            <p class="switch-link">
              已有账号？<a href="javascript:void(0)" @click="toggleCard">去登录</a>
            </p>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Right: hero -->
    <div class="login-hero">
      <div class="hero-content">
        <h2>安全 &middot; 高效 &middot; 便捷</h2>
        <p>您的智慧出行伙伴</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ---- brand header inside form panel ---- */
.form-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 28px;
}

.form-brand strong,
.form-brand small {
  display: block;
}

.form-brand strong {
  font-size: 20px;
}
.form-brand small {
  margin-top: 4px;
  color: #66717a;
}

.form-brand-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  color: #fff;
  background: #1f6f78;
  font-weight: 700;
  font-size: 20px;
}

/* ---- card scene & panel ---- */
.card-scene {
  position: relative;
}

.card-panel h3 {
  margin: 0 0 20px;
  font-size: 22px;
}

/* ---- form error text ---- */
.form-error {
  margin: -8px 0 12px;
  color: #e64545;
  font-size: 13px;
}

/* ---- switch link ---- */
.switch-link {
  margin: 18px 0 0;
  text-align: center;
  color: #8590a0;
  font-size: 14px;
}
.switch-link a {
  color: #1f6f78;
  text-decoration: none;
  font-weight: 600;
}
.switch-link a:hover {
  text-decoration: underline;
}

/* ---- welcome overlay ---- */
.welcome-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
}

.welcome-card {
  text-align: center;
}

.welcome-check {
  display: inline-grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #1f6f78;
  color: #fff;
  font-size: 32px;
  margin-bottom: 18px;
}

.welcome-card h2 {
  margin: 0;
  font-size: 24px;
  color: #20252b;
}

.welcome-card p {
  margin: 8px 0 0;
  color: #8590a0;
}

.welcome-fade-enter-active,
.welcome-fade-leave-active {
  transition: opacity 0.35s ease;
}
.welcome-fade-enter-from,
.welcome-fade-leave-to {
  opacity: 0;
}

/* ---- card flip transition ---- */
.card-flip-enter-active {
  transition: all 0.28s ease-out;
}
.card-flip-leave-active {
  transition: all 0.2s ease-in;
}
.card-flip-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.card-flip-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

/* ---- hero panel ---- */
.login-hero {
  padding: 54px;
  background:
    linear-gradient(rgba(20, 68, 73, 0.78), rgba(20, 68, 73, 0.78)),
    url("https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1600&q=80");
  background-size: cover;
  background-position: center;
  color: #fff;
  display: flex;
  align-items: flex-end;
}

.hero-content h2 {
  max-width: 620px;
  margin: 0;
  font-size: 36px;
  line-height: 1.2;
  letter-spacing: 0;
}

.hero-content p {
  margin: 10px 0 0;
  font-size: 18px;
  opacity: 0.85;
}
</style>
