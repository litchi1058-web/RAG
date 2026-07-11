<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <div class="logo-circle">
            <el-icon :size="36" color="#fff"><Search /></el-icon>
          </div>
        </div>
        <h1 class="login-title">病虫害智能诊断系统</h1>
        <p class="login-subtitle">登录您的账户，开始智能诊断之旅</p>
      </div>

      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <div class="form-item-wrapper">
          <div class="input-group">
            <div class="input-icon">
              <el-icon :size="18" color="#9ca3af"><User /></el-icon>
            </div>
            <input
              v-model="form.username"
              type="text"
              placeholder="用户名"
              class="custom-input"
              @keyup.enter="handleLogin"
            />
          </div>
        </div>

        <div class="form-item-wrapper">
          <div class="input-group">
            <div class="input-icon">
            <el-icon :size="18" color="#9ca3af"><Lock /></el-icon>
          </div>
          <input
            v-model="form.password"
            type="password"
            placeholder="密码"
            class="custom-input"
            :class="{ 'show-password': showPassword }"
            @keyup.enter="handleLogin"
          />
          <div class="password-toggle" @click="showPassword = !showPassword">
            <el-icon :size="18" color="#9ca3af"><View v-if="showPassword" /><Hide v-else /></el-icon>
          </div>
        </div>
      </div>

      <div class="role-tips">
        <div class="tip-item farmer-tip">
          <span class="tip-icon">🌾</span>
          <span class="tip-text">农户：拍照识别病虫害，获取防治方案</span>
        </div>
        <div class="tip-item data-tip">
          <span class="tip-icon">📊</span>
          <span class="tip-text">数据管理员：维护知识库，监控系统运行</span>
        </div>
        <div class="tip-item admin-tip">
          <span class="tip-icon">👑</span>
          <span class="tip-text">管理员：全面系统管理与用户权限控制</span>
        </div>
      </div>

      <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          class="login-btn"
          native-type="button"
        >
          {{ loading ? '登录中...' : '登 录' }}
        </el-button>

      </el-form>

      <div class="login-footer">
        <span>还没有账号？</span>
        <span class="create-link" @click="showRegister = true">立即注册</span>
      </div>
    </div>

    <div class="login-footer-text">
      <span>农业科技 · 智能诊断 · 精准防治</span>
    </div>

    <el-dialog
      v-model="showRegister"
      title="注册账号"
      width="400px"
      :close-on-click-modal="false"
      class="register-dialog"
    >
      <el-form :model="registerForm" @submit.prevent="handleRegister" class="register-form">
        <el-form-item>
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱（选填）"
            size="large"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取 消</el-button>
        <el-button type="primary" :loading="registerLoading" @click="handleRegister">注 册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Search, View, Hide } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)
const showPassword = ref(false)
const showRegister = ref(false)
const registerLoading = ref(false)
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

const handleLogin = async () => {
  if (!form.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.value.password) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)
    } else {
      const role = sessionStorage.getItem('role')
      if (role === 'farmer') {
        router.push('/recognition/detect')
      } else {
        router.push('/')
      }
    }
  } catch (e) {
    // 错误由拦截器处理
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerForm.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!registerForm.value.password) {
    ElMessage.warning('请输入密码')
    return
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  registerLoading.value = true
  try {
    const response = await fetch('/api/auth/register/public', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.value.username,
        password: registerForm.value.password,
        email: registerForm.value.email || ''
      })
    })
    const data = await response.json()
    if (response.ok) {
      ElMessage.success('注册成功，请登录')
      showRegister.value = false
      registerForm.value = { username: '', password: '', confirmPassword: '', email: '' }
    } else {
      ElMessage.error(data.message || '注册失败')
    }
  } catch (e) {
    ElMessage.error('注册失败，请稍后重试')
  } finally {
    registerLoading.value = false
  }
}


</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #166534 0%, #2e7d32 40%, #4caf50 70%, #a5d6a7 100%);
  position: relative;
  padding: 20px;
}

.login-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(20, 40, 20, 0.7) 0%, rgba(46, 125, 50, 0.55) 50%, rgba(76, 175, 80, 0.45) 100%);
}

.login-card {
  width: 520px;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 56px 48px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-logo {
  margin-bottom: 20px;
}

.logo-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  box-shadow: 0 8px 24px rgba(34, 197, 94, 0.4);
}

.login-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: -0.5px;
}

.login-subtitle {
  margin: 0;
  font-size: 15px;
  color: #6b7280;
  font-weight: 400;
}

.login-form {
  margin-bottom: 8px;
}

.form-item-wrapper {
  margin-bottom: 20px;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1.5px solid #e5e7eb;
  border-radius: 16px;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.input-group:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.input-group:focus-within {
  border-color: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.15), 0 4px 20px rgba(34, 197, 94, 0.08);
  transform: translateY(-1px);
}

.input-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #f3f4f6;
  transition: all 0.3s;
}

.input-group:focus-within .input-icon {
  color: #22c55e;
}

.custom-input {
  flex: 1;
  height: 52px;
  padding: 0 16px;
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  background: transparent;
  border: none;
  outline: none;
}

.custom-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.password-toggle {
  width: 48px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #9ca3af;
}

.password-toggle:hover {
  color: #22c55e;
}


.role-tips {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.tip-icon {
  font-size: 14px;
}

.tip-text {
  color: #6b7280;
}

.farmer-tip .tip-text { color: #22c55e; }
.data-tip .tip-text { color: #d97706; }
.admin-tip .tip-text { color: #dc2626; }

.login-btn {
  width: 100%;
  border-radius: 12px !important;
  height: 50px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(34, 197, 94, 0.4);
  transition: all 0.2s ease !important;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.5);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  padding-top: 8px;
  font-size: 14px;
  color: #6b7280;
}

.create-link {
  color: #22c55e;
  font-weight: 600;
  cursor: pointer;
  margin-left: 4px;
  transition: color 0.2s;
}

.create-link:hover {
  color: #16a34a;
  text-decoration: underline;
}

.login-footer-text {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.login-footer-text span {
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(8px);
}

@media (max-width: 640px) {
  .login-card {
    padding: 32px 24px;
    border-radius: 16px;
  }

  .login-title {
    font-size: 20px;
  }

  .login-subtitle {
    font-size: 14px;
  }

  .logo-circle {
    width: 56px;
    height: 56px;
  }

}
</style>
