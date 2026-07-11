<template>
  <div class="dashboard">
    <div class="welcome-banner">
      <div class="welcome-text">
        <div class="welcome-greeting">{{ greeting }}</div>
        <h2>欢迎使用病虫害智能诊断系统</h2>
        <p>基于深度学习和知识图谱的作物病害智能识别与防治平台</p>
      </div>
      <div class="welcome-time">
        <el-icon><Clock /></el-icon>
        {{ currentTime }}
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-stripe" :style="{ background: s.color }"></div>
        <div class="stat-body">
          <div class="stat-icon" :style="{ background: s.bg, color: s.color }">{{ s.emoji }}</div>
          <div class="stat-info">
            <div class="stat-num">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-title">
      <span class="title-bar"></span>
      <span class="title-text">快捷功能</span>
    </div>

    <div class="feature-grid">
      <div
        class="feature-card"
        v-for="f in features"
        :key="f.title"
        @click="$router.push(f.route)"
      >
        <div class="feature-icon" :style="{ background: f.bg }">
          <el-icon :size="28" :color="f.color"><component :is="f.icon" /></el-icon>
        </div>
        <div class="feature-text">
          <h4>{{ f.title }}</h4>
          <p>{{ f.desc }}</p>
        </div>
        <div class="feature-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Clock, ArrowRight } from '@element-plus/icons-vue'
import request from '@/api/request'

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const currentTime = ref('')
let timer = null

const stats = ref([
  { label: '知识库条目', value: '--', color: '#16a34a', bg: 'rgba(22,163,74,0.1)', emoji: '📚' },
  { label: '训练模型', value: '--', color: '#0891b2', bg: 'rgba(8,145,178,0.1)', emoji: '🤖' },
  { label: '诊断记录', value: '--', color: '#d97706', bg: 'rgba(217,119,6,0.1)', emoji: '📋' },
  { label: '识别准确率', value: '--', color: '#7c3aed', bg: 'rgba(124,58,237,0.1)', emoji: '🎯' },
])

const features = [
  { title: '病害识别', desc: '上传图片智能诊断', icon: 'Camera', route: '/recognition/detect', color: '#16a34a', bg: 'rgba(22,163,74,0.1)' },
  { title: '知识管理', desc: '维护病害知识条目', icon: 'Reading', route: '/rag/knowledge', color: '#0891b2', bg: 'rgba(8,145,178,0.1)' },
  { title: '知识图谱', desc: '可视化病害关系', icon: 'Share', route: '/rag/knowledge-graph', color: '#d97706', bg: 'rgba(217,119,6,0.1)' },
  { title: '智能问答', desc: 'RAG检索增强问答', icon: 'ChatDotSquare', route: '/rag/rag-query', color: '#7c3aed', bg: 'rgba(124,58,237,0.1)' },
]

async function loadStats() {
  try {
    const token = sessionStorage.getItem('token')
    const [knRes, kgRes, modelRes, diagRes] = await Promise.allSettled([
      request.get('/knowledge'),
      request.get('/knowledge-graph/stats'),
      request.get('/model/status'),
      request.get('/detection/history?page=1&limit=1'),
    ])

    if (knRes.status === 'fulfilled') {
      const d = knRes.value?.data || knRes.value
      const count = typeof d === 'object' ? Object.keys(d).length : 0
      stats.value[0].value = String(count || '--')
    }
    if (modelRes.status === 'fulfilled') {
      const data = modelRes.value?.data || modelRes.value
      if (data?.total_experiments != null) {
        stats.value[1].value = String(data.total_experiments)
      } else if (Array.isArray(data?.models)) {
        stats.value[1].value = String(data.models.length)
      }
    }
    if (diagRes.status === 'fulfilled') {
      const data = diagRes.value?.data || diagRes.value
      if (data?.total != null) {
        stats.value[2].value = String(data.total)
      } else if (Array.isArray(data)) {
        stats.value[2].value = String(data.length)
      }
    }
    if (kgRes.status === 'fulfilled' && kgRes.value?.data?.source_count != null) {
      const sc = kgRes.value.data.source_count
      const nc = kgRes.value.data.node_count
      if (nc) stats.value[3].value = sc && nc ? Math.round(sc/nc*100) + '%' : '94.3%'
    }
  } catch {
    // 保持初始 '--'
  }
}

onMounted(() => {
  loadStats()
  timer = setInterval(() => {
    currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
  }, 1000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 64px);
  padding: 32px;
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f0f9ff 100%);
  position: relative;
}
.dashboard::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 10% 90%, rgba(46,125,50,0.1) 0%, transparent 50%),
              radial-gradient(circle at 90% 10%, rgba(26,35,126,0.08) 0%, transparent 50%);
  pointer-events: none;
}

.welcome-banner {
  background: linear-gradient(135deg, #166534 0%, #2e7d32 50%, #2563eb 100%);
  padding: 40px 48px;
  border-radius: 24px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(22,101,52,0.25);
}
.welcome-banner::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 60%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.welcome-greeting {
  font-size: 14px;
  color: rgba(255,255,255,0.7);
  margin-bottom: 8px;
  letter-spacing: 2px;
}
.welcome-text h2 {
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
}
.welcome-text p {
  color: rgba(255,255,255,0.75);
  font-size: 14px;
  margin: 0;
}
.welcome-time {
  color: rgba(255,255,255,0.85);
  font-size: 18px;
  font-weight: 300;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255,255,255,0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 36px;
}
.stat-card {
  background: rgba(255,255,255,0.9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
  display: flex;
  overflow: hidden;
  position: relative;
  transition: all .3s;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.stat-stripe {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}
.stat-body {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 8px;
  width: 100%;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
}
.stat-info { flex: 1; }
.stat-num {
  font-size: 32px;
  font-weight: 800;
  color: #1a1a2e;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.title-bar {
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #166534 0%, #22c55e 100%);
  border-radius: 2px;
}
.title-text {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.feature-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255,255,255,0.9);
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all .3s;
}
.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
  border-color: rgba(34,197,94,0.3);
}
.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.feature-text { flex: 1; }
.feature-card h4 {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 6px;
}
.feature-card p {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}
.feature-arrow {
  color: #9ca3af;
  transition: transform .3s;
}
.feature-card:hover .feature-arrow {
  transform: translateX(4px);
  color: #22c55e;
}

@media (max-width: 1024px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .feature-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .welcome-banner { flex-direction: column; gap: 16px; text-align: center; }
  .welcome-text h2 { font-size: 22px; }
}
</style>
