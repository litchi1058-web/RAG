<template>
  <div class="logout-container">
    <el-card class="logout-card">
      <template #header>
        <div class="logout-header">
          <el-icon :size="32" color="#1890FF"><SwitchButton /></el-icon>
          <span>退出登录</span>
        </div>
      </template>
      <div class="logout-content">
        <el-alert title="已成功退出登录" type="success" :closable="false" />
        <p style="margin-top: 16px; color: #666;">正在返回登录页面...</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()

onMounted(() => {
  sessionStorage.clear()
  setTimeout(() => {
    router.push('/login')
  }, 1500)
})
</script>

<style scoped>
.logout-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.logout-card {
  width: 400px;
  text-align: center;
}

.logout-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.logout-content {
  padding: 20px 0;
}
</style>