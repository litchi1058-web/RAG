<template>
  <div id="app-root">
    <transition name="fade">
      <div v-if="globalLoading" class="app-loading-overlay">
        <div class="app-loading-spinner">
          <el-icon class="app-loading-icon" :size="40"><Loading /></el-icon>
          <p>加载中...</p>
        </div>
      </div>
    </transition>
    <router-view v-slot="{ Component, route }">
      <transition name="fade-slide" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const globalLoading = ref(true)

onMounted(async () => {
  try {
    if (auth.token && typeof auth.fetchMe === 'function') {
      await auth.fetchMe()
    }
  } finally {
    setTimeout(() => { globalLoading.value = false }, 300)
  }
})
</script>

<style>
#app-root { height: 100%; position: relative; }
.app-loading-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: var(--bg-page, #f0f2f5);
  display: flex; align-items: center; justify-content: center;
}
.app-loading-spinner { text-align: center; color: var(--text-secondary, #909399); }
.app-loading-icon {
  animation: app-loading-rotate 1.2s linear infinite;
  color: var(--primary, #409eff);
}
.app-loading-spinner p { margin-top: 12px; font-size: 14px; color: var(--text-secondary, #909399); }
@keyframes app-loading-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
