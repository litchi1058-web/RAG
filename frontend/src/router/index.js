import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/SimpleLayout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('@/views/Home.vue') },
      { path: 'about', name: 'About', component: () => import('@/views/About.vue') }
    ]
  },
  {
    path: '/logout',
    name: 'Logout',
    component: () => import('@/views/Logout.vue'),
    meta: { public: true }
  },
  {
    path: '/recognition',
    name: 'RecognitionRoot',
    component: () => import('@/layouts/RecognitionLayout.vue'),
    redirect: '/recognition/detect',
    children: [
      { path: 'detect', name: 'Recognition', component: () => import('@/views/Recognition.vue'), meta: { title: '病害识别', icon: 'Camera' } }
    ]
  },
  {
    path: '/rag',
    component: () => import('@/layouts/RagLayout.vue'),
    redirect: '/rag/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '数据概览', icon: 'DataAnalysis' } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('@/views/Knowledge.vue'), meta: { title: '知识管理', icon: 'Reading' } },
      { path: 'knowledge-graph', name: 'KnowledgeGraph', component: () => import('@/views/KnowledgeGraph.vue'), meta: { title: '知识图谱', icon: 'Share' } },
      { path: 'rag-query', name: 'RagQuery', component: () => import('@/views/ChatQa.vue'), meta: { title: '智能问答', icon: 'ChatDotSquare' } },
      { path: 'diagnosis', name: 'Diagnosis', component: () => import('@/views/Diagnosis.vue'), meta: { title: '诊断记录', icon: 'Document' } }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/SimpleLayout.vue'),
    redirect: '/admin/users',
    children: [
      { path: 'users', name: 'UserManagement', component: () => import('@/views/admin/UserManagement.vue'), meta: { title: '用户管理' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ─── 路由守卫：JWT + 角色权限 ───
router.beforeEach((to, from, next) => {
  const token = sessionStorage.getItem('token')
  const role = sessionStorage.getItem('role')

  // 根路径未登录 → 跳转登录页
  if (to.path === '/' && !token) {
    return next({ name: 'Login' })
  }

  // 公开页（登录、退出）无需登录
  if (to.meta.public) {
    if (token && to.name === 'Login') {
      return next({ name: 'Home' })
    }
    return next()
  }

  // 未登录 → 跳转登录页
  if (!token) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // 已登录但无 role（token 异常）→ 重新登录
  if (!role) {
    sessionStorage.clear()
    return next({ name: 'Login' })
  }

  // 角色路由权限校验
  const roleRoutes = {
    admin: null,
    data_manager: ['Home', 'Recognition', 'Dashboard', 'Knowledge', 'KnowledgeGraph',
                   'RagQuery', 'Diagnosis'],
    farmer: ['Home', 'Recognition', 'RagQuery', 'Diagnosis'],
  }

  const allowed = roleRoutes[role] || null
  if (allowed !== null && to.name && !allowed.includes(to.name)) {
    return next({ name: 'Home' })
  }

  next()
})

export default router
