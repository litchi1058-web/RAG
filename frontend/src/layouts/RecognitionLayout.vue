<template>
  <div class="ms-layout">
    <header class="ms-header">
      <div class="ms-header-left">
        <el-tooltip content="返回首页" placement="bottom">
          <span class="home-btn" @click="$router.push('/')">🏠</span>
        </el-tooltip>
        <span class="brand-divider"></span>
        <span class="brand-icon">🔬</span>
        <span class="brand-text">识别诊断</span>
      </div>
      <nav class="ms-tabs">
        <div v-for="item in menuItems" :key="item.path"
          class="ms-tab" :class="{ active: $route.path === item.path }"
          @click="navigate(item.path)">
          <el-icon :size="15"><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
          <div class="tab-indicator" v-if="$route.path === item.path"></div>
        </div>
      </nav>
      <div class="ms-header-right">
        <el-tag size="small" effect="light" class="status-tag" :style="{ background: roleColor + '15', color: roleColor, borderColor: roleColor + '30' }">
          {{ roleIcon }} {{ roleLabel }}
        </el-tag>
        <el-dropdown @command="handleCommand" trigger="click">
          <span class="ms-user">
            <el-avatar :size="26" :style="{ background: roleColor }">{{ username.charAt(0).toUpperCase() }}</el-avatar>
            <span class="user-name">{{ username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="home">返回首页</el-dropdown-item>
              <el-dropdown-item command="switch" icon="SwitchButton">切换用户</el-dropdown-item>
              <el-dropdown-item command="logout" icon="SwitchButton" divided type="danger">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-tooltip content="退出登录" placement="bottom">
          <span class="logout-btn" @click="handleLogout">⏻</span>
        </el-tooltip>
      </div>
    </header>
    <main class="ms-content"><router-view /></main>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
const router = useRouter()
const route = useRoute()
const username = computed(() => sessionStorage.getItem('username') || '')
const role = computed(() => sessionStorage.getItem('role') || '')
const roleColor = computed(() => ({ admin:'#dc2626', data_manager:'#d97706', farmer:'#22c55e' }[role.value] || '#6b7280'))
const roleIcon = computed(() => ({ admin:'👑', data_manager:'📊', farmer:'🌾' }[role.value] || '👤'))
const roleLabel = computed(() => ({ admin:'管理员', data_manager:'数据管理员', farmer:'农户' }[role.value] || ''))
const menuItems = [
  { path: '/recognition/detect', title: '病害识别', icon: Search },
]
function navigate(path) { if (route.path !== path) router.push(path) }
function handleCommand(cmd) {
  if (cmd === 'logout') handleLogout()
  else if (cmd === 'switch') { sessionStorage.clear(); router.push('/login') }
  else if (cmd === 'home') router.push('/')
}
function handleLogout() { sessionStorage.clear(); router.push('/login') }
</script>
<style scoped>
.ms-layout { height: 100vh; display: flex; flex-direction: column; background: transparent; overflow: hidden; }
.ms-header { height: 48px; min-height: 48px; background: #fff; border-bottom: 1px solid #e8eaed; display: flex; align-items: center; padding: 0 12px; gap: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); z-index: 100; }
.ms-header-left { flex-shrink: 0; display: flex; align-items: center; gap: 8px; }
.home-btn { font-size: 16px; cursor: pointer; padding: 4px 6px; border-radius: 6px; transition: background .2s; line-height: 1; }
.home-btn:hover { background: #f0f1f3; }
.brand-divider { width: 1px; height: 20px; background: #e0e0e0; }
.brand-icon { font-size: 18px; }
.brand-text { font-size: 14px; font-weight: 600; color: #1a1a2e; }
.ms-tabs { flex: 1; display: flex; align-items: stretch; gap: 1px; margin: 0 2px; overflow-x: auto; scrollbar-width: none; height: 100%; }
.ms-tab { display: flex; align-items: center; gap: 4px; padding: 0 12px; font-size: 13px; color: #5f6368; cursor: pointer; white-space: nowrap; position: relative; border-radius: 6px 6px 0 0; transition: all .15s; }
.ms-tab:hover { background: #f0f1f3; color: #1a1a2e; }
.ms-tab.active { color: #4f6ef7; background: #f0f2f5; }
.tab-indicator { position: absolute; bottom: 0; left: 6px; right: 6px; height: 2px; background: #4f6ef7; border-radius: 2px 2px 0 0; }
.ms-header-right { flex-shrink: 0; display: flex; align-items: center; gap: 6px; }
.status-tag { font-size: 10px; padding: 0 6px; height: 22px; line-height: 22px; }
.ms-user { display: flex; align-items: center; gap: 5px; cursor: pointer; padding: 2px 6px; border-radius: 6px; transition: background .2s; }
.ms-user:hover { background: #f0f1f3; }
.user-name { font-size: 12px; color: #1a1a2e; max-width: 60px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.logout-btn { font-size: 16px; cursor: pointer; padding: 4px 6px; border-radius: 6px; transition: all .2s; line-height: 1; opacity: .5; }
.logout-btn:hover { opacity: 1; background: #fee; }
.ms-content { flex: 1; padding: 6px; overflow-y: auto; background: transparent; }
</style>
