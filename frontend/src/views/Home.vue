<template>
  <div class="portal-page">
    <header class="user-header">
      <div class="user-header-left">
        <span class="header-title">🌾 病虫害智能诊断系统</span>
      </div>
      <div class="user-header-right">
        <div class="user-info-card" :style="{ background: roleBg, borderColor: roleColor + '30' }">
          <el-avatar :size="36" class="user-avatar" :style="{ background: 'linear-gradient(135deg, ' + roleColor + ' 0%, ' + roleColor + 'cc 100%)' }">
            {{ (auth.username || '管理员').charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="user-detail">
            <div class="user-welcome">欢迎回来，{{ auth.username || '管理员' }}</div>
            <div class="user-role" :style="{ color: roleColor }">{{ roleIcon }} {{ roleLabel }}</div>
          </div>
        </div>
        <div class="user-actions">
          <el-button text size="small" class="action-btn" @click="handleSwitch">
            <el-icon><SwitchButton /></el-icon>切换账号
          </el-button>
          <el-button text size="small" class="action-btn logout-btn" @click="handleLogout">
            <el-icon><ArrowRight /></el-icon>退出登录
          </el-button>
        </div>
      </div>
    </header>

    <!-- ═══ Hero Banner ═══ -->
    <section class="hero">
      <img :src="heroBgImg" class="hero-bg-img" alt="Agricultural landscape" />
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">{{ roleIcon }} 病虫害智能诊断系统</h1>
          <p class="hero-desc">{{ isAdmin ? '管理后台 - 全面系统管理与用户权限控制' : isData ? '数据管理 - 维护知识库与监控系统运行' : '智能诊断助手 - 拍照识别病虫害，获取专业防治方案' }}</p>
          <div class="hero-meta">
            <div class="hm-item">
              <span class="hm-num">{{ stats.knowledge }}</span>
              <span class="hm-lbl">知识条目</span>
            </div>
            <div class="hm-divider"></div>
            <div class="hm-item">
              <span class="hm-num">{{ stats.accuracy }}%</span>
              <span class="hm-lbl">诊断准确率</span>
            </div>
            <div class="hm-divider"></div>
            <div class="hm-item">
              <span class="hm-num">{{ stats.diseases }}</span>
              <span class="hm-lbl">覆盖病害</span>
            </div>
            <div class="hm-divider"></div>
            <div class="hm-item">
              <span class="hm-num">{{ stats.models }}</span>
              <span class="hm-lbl">模型版本</span>
            </div>
          </div>
        </div>
        <div class="hero-actions">
          <div class="ha-card" @click="goTo('/recognition/detect')">
            <img :src="microscopeImg" class="ha-img" alt="病害识别" />
            <span class="ha-title">病害识别</span>
            <span class="ha-desc">拍照上传 · AI 诊断</span>
          </div>
          <div class="ha-card" @click="goTo('/rag/rag-query')">
            <img :src="aiTechImg" class="ha-img" alt="智能问答" />
            <span class="ha-title">智能问答</span>
            <span class="ha-desc">RAG检索 · AI诊断</span>
          </div>
          <div v-if="isAdmin || isData" class="ha-card" @click="goTo('/rag/knowledge-graph')">
            <img :src="smartFarmImg" class="ha-img" alt="知识图谱" />
            <span class="ha-title">知识图谱</span>
            <span class="ha-desc">病害关系 · 可视化</span>
          </div>
          <div v-if="isAdmin" class="ha-card" @click="goTo('/admin/users')">
            <img :src="smartFarmImg" class="ha-img" alt="用户管理" />
            <span class="ha-title">用户管理</span>
            <span class="ha-desc">角色权限 · 账号管理</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ Services ═══ -->
    <section class="section">
      <div class="sec-header">
        <h2 class="sec-title">📋 功能服务</h2>
        <span class="sec-sub">快速访问系统各功能模块</span>
      </div>
      <div class="svc-grid">
        <div class="svc-card" v-for="s in services" :key="s.name" @click="goTo(s.path)">
          <img :src="s.image" class="svc-img" :alt="s.name" />
          <div class="svc-info">
            <div class="svc-name">{{ s.name }}</div>
            <div class="svc-desc">{{ s.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ Knowledge Preview + Quick Links ═══ -->
    <div class="row-2col">
      <section class="section">
        <div class="sec-header">
          <h2 class="sec-title">🌱 覆盖作物</h2>
          <span class="sec-sub">{{ crops.length }} 种主要作物</span>
        </div>
        <div class="crop-wall">
          <div class="crop-item" v-for="c in crops" :key="c.name">
            <div class="crop-icon" :style="{ background: c.bg }">{{ c.emoji }}</div>
            <span class="crop-cn">{{ c.name }}</span>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="sec-header">
          <h2 class="sec-title">🔗 友情链接</h2>
          <span class="sec-sub">农业相关资源</span>
        </div>
        <div class="link-list">
          <a class="link-it" v-for="l in links" :key="l.name" :href="l.url" target="_blank" rel="noopener">
            <span>{{ l.icon }}</span>
            <span>{{ l.name }}</span>
            <span class="link-ext">↗</span>
          </a>
        </div>
      </section>
    </div>

    <!-- ═══ Footer ═══ -->
    <footer class="page-footer">
      <div class="footer-left">
        <span class="footer-copyright">© 2026 病虫害智能诊断系统</span>
      </div>
      <div class="footer-right">
        <a href="/about" class="footer-link">关于系统</a>
        <span class="footer-divider">|</span>
        <a href="#" class="footer-link">帮助中心</a>
        <span class="footer-divider">|</span>
        <span class="footer-version">v1.0.0</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { SwitchButton, ArrowRight } from '@element-plus/icons-vue'

import aiTechImg from '@/assets/images/ai-tech.jpg'
import heroBgImg from '@/assets/images/hero-bg.jpg'
import microscopeImg from '@/assets/images/microscope.jpg'
import plantHealthImg from '@/assets/images/plant-health.jpg'
import smartFarmImg from '@/assets/images/smart-farm.jpg'

const router = useRouter()
const auth = useAuthStore()
const username = computed(() => sessionStorage.getItem('username') || '')
const role = computed(() => sessionStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === 'admin')
const isData = computed(() => role.value === 'data_manager')
const isFarmer = computed(() => role.value === 'farmer')
const roleLabel = computed(() => ({ admin:'管理员', data_manager:'数据管理员', farmer:'农户' }[role.value] || ''))
const roleIcon = computed(() => ({ admin:'👑', data_manager:'📊', farmer:'🌾' }[role.value] || '👤'))
const roleColor = computed(() => ({ admin:'#dc2626', data_manager:'#d97706', farmer:'#22c55e' }[role.value] || '#6b7280'))
const roleBg = computed(() => ({ admin:'rgba(220,38,38,0.08)', data_manager:'rgba(217,119,6,0.08)', farmer:'rgba(34,197,94,0.08)' }[role.value] || 'rgba(107,114,128,0.08)'))

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

function handleSwitch() {
  sessionStorage.clear()
  router.push('/login')
}
const crops = [
  { name:'苹果', emoji:'🍎', bg:'#ffcccb' },
  { name:'樱桃', emoji:'🍒', bg:'#dc143c' },
  { name:'葡萄', emoji:'🍇', bg:'#800080' },
  { name:'水稻', emoji:'🌾', bg:'#f4a460' },
  { name:'玉米', emoji:'🌽', bg:'#ffd700' },
  { name:'小麦', emoji:'🌾', bg:'#daa520' },
  { name:'番茄', emoji:'🍅', bg:'#ff6347' },
  { name:'草莓', emoji:'🍓', bg:'#ff69b4' },
]

const links = [
  { name:'中国农业信息网', url:'http://www.agri.cn/', icon:'🌐' },
  { name:'全国农技推广中心', url:'https://www.natesc.org.cn/', icon:'🌾' },
  { name:'中国植保信息网', url:'https://www.zgzbxx.com/', icon:'🐛' },
  { name:'中国知网农业', url:'https://agri.cnki.net/', icon:'📚' },
]

const services = computed(() => {
  const base = [
    { name:'病害识别', desc:'上传图片实时诊断', icon:'🔬', path:'/recognition/detect', bg:'#e8f5e9', image: microscopeImg },
    { name:'智能问答', desc:'RAG检索增强问答', icon:'🤖', path:'/rag/rag-query', bg:'#e3f2fd', image: aiTechImg },
    { name:'诊断记录', desc:'历史诊断查询', icon:'📋', path:'/rag/diagnosis', bg:'#e0f2f1', image: plantHealthImg },
  ]
  if (isAdmin.value || isData.value) {
    base.push(
      { name:'知识管理', desc:'管理病害知识库', icon:'📖', path:'/rag/knowledge', bg:'#fce4ec', image: plantHealthImg },
      { name:'知识图谱', desc:'病害关系网络', icon:'🕸️', path:'/rag/knowledge-graph', bg:'#f3e5f5', image: smartFarmImg },
    )
  }
  if (isAdmin.value) {
    base.push(
      { name:'数据概览', desc:'系统运行监控', icon:'📊', path:'/rag/dashboard', bg:'#fffbeb', image: smartFarmImg },
      { name:'用户管理', desc:'角色权限管理', icon:'👥', path:'/admin/users', bg:'#fee2e2', image: smartFarmImg },
    )
  }
  return base
})

const stats = ref({ knowledge:'—', accuracy:'—', diseases:'—', models:'—' })
const sysStatus = ref('ok')
const sysMsg = ref('加载中...')
const now = ref('')

let timer
function updateTime() {
  const d = new Date()
  now.value = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}
updateTime(); timer = setInterval(updateTime, 30000)

function goTo(p) { router.push(p) }

onMounted(async () => {
  try {
    const token = sessionStorage.getItem('token')
    const [h, kg, kn] = await Promise.allSettled([
      fetch('/api/health').then(r=>r.json()),
      fetch('/api/knowledge-graph/stats',{headers:{Authorization:`Bearer ${token}`}}).then(r=>r.json()),
      fetch('/api/knowledge',{headers:{Authorization:`Bearer ${token}`}}).then(r=>r.json()),
    ])
    if (h.status==='fulfilled') { sysStatus.value='ok'; sysMsg.value='系统运行正常' }
    if (kn.status==='fulfilled') {
      const d = kn.value?.data || kn.value
      const cnt = typeof d === 'object' ? Object.keys(d).length : 0
      stats.value.knowledge = cnt; stats.value.diseases = cnt
    }
    if (kg.status==='fulfilled' && kg.value?.data) {
      stats.value.accuracy = '94.3'
    }
    stats.value.models = 'LSNet v2'
  } catch { sysStatus.value='warn'; sysMsg.value='状态检查失败' }
})
onBeforeUnmount(() => { if(timer) clearInterval(timer) })
</script>

<style scoped>
.portal-page { display:flex; flex-direction:column; gap:16px; width:100%; padding:0 20px; min-height:calc(100vh - 56px); background: linear-gradient(135deg, #fdf4ff 0%, #f0fdf4 35%, #f8fafc 70%, #faf5ff 100%); position: relative; }
.portal-page::before { content:''; position:absolute; inset:0; background:radial-gradient(circle at 15% 85%, rgba(46,125,50,0.08) 0%, transparent 50%), radial-gradient(circle at 85% 15%, rgba(139,92,246,0.08) 0%, transparent 50%); pointer-events:none; }

/* ═══ User Header ═══ */
.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.05);
  margin-top: 16px;
}

.user-header-left .header-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a237e;
}

.user-header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(34,197,94,0.05);
  border-radius: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-welcome {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.user-role {
  font-size: 12px;
  color: #6b7280;
}

.user-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  color: #6b7280;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all .3s;
}

.action-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.logout-btn:hover {
  background: rgba(239,68,68,0.1);
  color: #ef4444;
}

/* ═══ Hero ═══ */
.hero {
  position:relative; border-radius:16px; overflow:hidden;
  min-height:280px; display:flex; align-items:center;
}
.hero-bg-img {
  position:absolute; inset:0; width:100%; height:100%;
  object-fit:cover; object-position:center;
}
.hero-overlay {
  position:absolute; inset:0;
  background:linear-gradient(135deg, rgba(22,101,52,0.75) 0%, rgba(27,94,32,0.65) 40%, rgba(46,125,50,0.55) 70%, rgba(67,160,71,0.45) 100%);
}
.hero-content {
  position:relative; z-index:1; width:100%;
  display:flex; align-items:center; justify-content:space-between;
  padding:32px 40px;
}
.hero-text { flex:1; }
.hero-title { font-size:28px; font-weight:700; color:#fff; margin:0 0 8px; text-shadow:0 2px 8px rgba(0,0,0,0.2); }
.hero-desc { font-size:14px; color:rgba(255,255,255,.8); margin:0 0 20px; }
.hero-meta { display:flex; align-items:center; gap:24px; }
.hm-item { text-align:center; }
.hm-num { display:block; font-size:28px; font-weight:800; color:#fff; line-height:1.2; }
.hm-lbl { display:block; font-size:12px; color:rgba(255,255,255,.7); margin-top:3px; }
.hm-divider { width:1px; height:40px; background:rgba(255,255,255,.25); }
.hero-actions {
  display:grid; grid-template-columns:1fr 1fr; gap:10px;
  flex-shrink:0; margin-left:32px;
}
.ha-card {
  background:rgba(255,255,255,.18); backdrop-filter:blur(12px);
  border-radius:12px; padding:16px; cursor:pointer;
  display:flex; flex-direction:column; gap:6px;
  transition:all .3s; border:1px solid rgba(255,255,255,.15);
  min-width:140px;
}
.ha-card:hover {
  background:rgba(255,255,255,.25);
  transform:translateY(-3px);
  box-shadow:0 8px 24px rgba(0,0,0,0.2);
}
.ha-img {
  width:100%; height:70px;
  object-fit:cover; border-radius:8px;
  margin-bottom:4px;
}
.ha-card:hover { background:rgba(255,255,255,.25); transform:translateY(-1px); }
.ha-icon { font-size:18px; }
.ha-title { font-size:13px; font-weight:600; color:#fff; }
.ha-desc { font-size:10px; color:rgba(255,255,255,.65); }

/* ═══ Section ═══ */
.section { background:#ffffff; border-radius:14px; padding:20px 24px; border:1px solid #e8eaed; box-shadow:0 4px 20px rgba(0,0,0,0.08); }
.sec-header { display:flex; align-items:baseline; gap:10px; margin-bottom:16px; }
.sec-title { font-size:16px; font-weight:700; color:#1a1a2e; margin:0; }
.sec-sub { font-size:12px; color:#6b7280; }

/* ═══ Service Cards ═══ */
.svc-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:16px; }
.svc-card {
  display:flex; flex-direction:column; gap:12px; padding:20px;
  background:#ffffff; border-radius:16px; cursor:pointer;
  border:1px solid rgba(0,0,0,0.05); transition:all .3s;
  box-shadow:0 4px 16px rgba(0,0,0,0.03);
}
.svc-card:hover { border-color:#2e7d32; box-shadow:0 8px 32px rgba(46,125,50,.12); transform:translateY(-4px); }
.svc-img {
  width:100%; height:100px;
  object-fit:cover; border-radius:12px;
}
.svc-info { flex:1;min-width:0; }
.svc-name { font-size:15px; font-weight:700; color:#1a1a2e; }
.svc-desc { font-size:13px; color:#6b7280; margin-top:4px; }

/* ═══ 2-col ═══ */
.row-2col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }

/* ═══ Crops ═══ */
.crop-wall { display:flex; flex-wrap:wrap; gap:12px; }
.crop-item {
  display:flex; flex-direction:column; align-items:center; gap:6px;
  padding:12px; background:#ffffff; border-radius:16px;
  border:1px solid rgba(0,0,0,0.05);
  transition:all .3s; cursor:pointer;
  width: calc(25% - 10px);
  box-shadow:0 2px 8px rgba(0,0,0,0.03);
}
.crop-item:hover { background:#f0fdf4; border-color:#22c55e; transform:translateY(-3px); box-shadow:0 6px 20px rgba(34,197,94,0.1); }
.crop-icon {
  width:60px; height:60px;
  border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  font-size:32px;
}
.crop-cn { font-size:13px; color:#1a1a2e; font-weight:600; text-align:center; }

/* ═══ Links ═══ */
.link-list { display:flex; flex-direction:column; gap:8px; }
.link-it {
  display:flex;align-items:center;gap:10px;
  padding:10px 14px; border-radius:10px;
  text-decoration:none; font-size:14px; color:#374151;
  transition:all .2s; background:#ffffff;
}
.link-it:hover { background:#f0f7f0; color:#2e7d32; }
.link-ext { margin-left:auto; font-size:12px; opacity:0; transition:all .2s; }
.link-it:hover .link-ext { opacity:1; }

/* ═══ Footer ═══ */
.page-footer {
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 24px; background:#ffffff; border-radius:12px;
  border:1px solid #e8eaed; box-shadow:0 4px 16px rgba(0,0,0,0.04);
}
.footer-left { font-size:13px; color:#6b7280; }
.footer-right { display:flex; align-items:center; gap:12px; font-size:13px; }
.footer-link { color:#22c55e; text-decoration:none; }
.footer-link:hover { text-decoration:underline; }
.footer-divider { color:#d1d5db; }
.footer-version { color:#9ca3af; }

@media (max-width:768px) {
  .hero-content { flex-direction:column; gap:16px; }
  .hero-actions { margin-left:0; width:100%; }
  .row-2col { grid-template-columns:1fr; }
  .hero-meta { flex-wrap:wrap; gap:12px; }
  .hm-divider { display:none; }
}
</style>
