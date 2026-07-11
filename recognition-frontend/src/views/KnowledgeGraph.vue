<template>
  <div class="kg-page">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <el-icon :size="28" color="#2563eb"><Monitor /></el-icon>
        <h2>智能诊断</h2>
        <p>病虫害识别系统</p>
      </div>
      <div class="nav-list">
        <div class="nav-item" @click="$router.push('/')">
          <i class="fas fa-home"></i><span>病害诊断</span>
        </div>
        <div class="nav-item" @click="$router.push('/chat')">
          <i class="fas fa-robot"></i><span>AI助手</span>
        </div>
        <div class="nav-item active" @click="$router.push('/knowledge-graph')">
          <i class="fas fa-project-diagram"></i><span>知识图谱</span>
        </div>
        <div class="nav-item" @click="$router.push('/about')">
          <i class="fas fa-info-circle"></i><span>关于系统</span>
        </div>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="main-content">
      <div class="page-header">
        <h1>🔗 病害知识图谱</h1>
        <p>可视化展示作物、病害、症状及防治措施之间的关联关系</p>
      </div>

      <div class="graph-layout">
        <!-- 控制面板 -->
        <div class="control-panel">
          <el-input v-model="searchQuery" placeholder="搜索节点..." clearable @input="onSearch" />
          <div class="filter-section">
            <h3>节点类型</h3>
            <div class="type-filters">
              <el-checkbox v-for="t in nodeTypes" :key="t.key" v-model="t.checked" @change="updateFilter">
                {{ t.label }}
              </el-checkbox>
            </div>
          </div>
          <div class="stats">
            <div class="stat"><span class="num">{{ filteredNodes.length }}</span> 节点</div>
            <div class="stat"><span class="num">{{ filteredEdges.length }}</span> 关系</div>
          </div>
          <el-button @click="resetView" :icon="'Refresh'" size="small">重置视图</el-button>
          <el-button @click="fetchFromBackend" :icon="'Download'" size="small">加载数据</el-button>

          <!-- 节点详情 -->
          <div v-if="selectedNode" class="node-detail">
            <h4>{{ selectedNode.name }}</h4>
            <el-tag size="small">{{ selectedNode.category || selectedNode.type }}</el-tag>
            <p v-if="selectedNode.description">{{ selectedNode.description }}</p>
          </div>
        </div>

        <!-- 图谱画布 -->
        <div class="graph-canvas" ref="graphRef">
          <svg :width="w" :height="h">
            <!-- 关系线 -->
            <line
              v-for="(e, i) in filteredEdges"
              :key="'e'+i"
              :x1="pos(e.source).x" :y1="pos(e.source).y"
              :x2="pos(e.target).x" :y2="pos(e.target).y"
              :class="['edge', { highlight: isEdgeHL(e) }]"
              :marker-end="isEdgeHL(e) ? 'url(#a-hl)' : 'url(#a)'"
            />
            <!-- 节点 -->
            <g
              v-for="node in filteredNodes"
              :key="node.id || node.name"
              :class="['node-g', { selected: selectedNode?.id === node.id || selectedNode?.name === node.name }]"
              @click="selectNode(node)"
              style="cursor:pointer"
            >
              <circle
                :cx="pos(node.id || node.name).x"
                :cy="pos(node.id || node.name).y"
                :r="nodeRadius(node)"
                :class="'node-' + typeColor(node)"
              />
              <text
                :x="pos(node.id || node.name).x"
                :y="pos(node.id || node.name).y + 4"
                text-anchor="middle" font-size="16"
              >{{ typeIcon(node) }}</text>
              <text
                :x="pos(node.id || node.name).x"
                :y="pos(node.id || node.name).y + nodeRadius(node) + 16"
                text-anchor="middle" font-size="12"
                class="node-label"
              >{{ node.name.length > 8 ? node.name.slice(0,6)+'..' : node.name }}</text>
            </g>
          </svg>
        </div>
      </div>

      <!-- 图例 -->
      <div class="legend">
        <span v-for="t in nodeTypes" :key="t.key" class="legend-item">
          <span class="dot" :class="t.key"></span>
          {{ t.label }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getKnowledgeGraph } from '@/api'

const graphRef = ref(null)
const w = 1400
const h = 900
const searchQuery = ref('')
const nodePositions = ref({})
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)

const nodeTypes = reactive([
  { key: 'crop', label: '🌾 作物', checked: true },
  { key: 'disease', label: '🦠 病害', checked: true },
  { key: 'symptom', label: '⚠️ 症状', checked: true },
  { key: 'treatment', label: '💊 防治', checked: true },
  { key: 'disease_type', label: '📋 类型', checked: true }
])

const activeTypes = computed(() =>
  nodeTypes.filter(t => t.checked).map(t => t.key)
)

const filteredNodes = computed(() => {
  let list = nodes.value.filter(n => activeTypes.value.includes(n.category || n.type))
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(n => (n.name || '').toLowerCase().includes(q))
  }
  return list
})

const filteredEdges = computed(() => {
  const names = new Set(filteredNodes.value.map(n => n.id || n.name))
  return edges.value.filter(e =>
    (names.has(e.source) || names.has(e.source.id || e.source.name)) &&
    (names.has(e.target) || names.has(e.target.id || e.target.name))
  )
})

function typeColor(node) {
  const t = node.category || node.type
  if (t === 'crop') return 'crop'
  if (t === 'disease') return 'disease'
  if (t === 'symptom') return 'symptom'
  if (t === 'treatment' || t === 'medicine') return 'treatment'
  return 'default'
}

function typeIcon(node) {
  const t = node.category || node.type
  if (t === 'crop') return '🌾'
  if (t === 'disease') return '🦠'
  if (t === 'symptom') return '⚠️'
  if (t === 'treatment' || t === 'medicine') return '💊'
  return '📋'
}

function nodeRadius(node) {
  const t = node.category || node.type
  if (t === 'crop') return 32
  if (t === 'disease') return 28
  return 24
}

function pos(id) {
  return nodePositions.value[id] || { x: 100, y: 100 }
}

function isEdgeHL(e) {
  if (!selectedNode.value) return false
  const name = selectedNode.value.id || selectedNode.value.name
  return e.source === name || e.target === name ||
    e.source?.id === name || e.target?.id === name
}

function selectNode(node) {
  selectedNode.value = node
}

function resetView() {
  selectedNode.value = null
  searchQuery.value = ''
}

function updateFilter() {}

function onSearch() {
  // reactive filtering via computed
}

function layoutNodes(dataNodes) {
  const pos = {}
  const cols = { crop: 0, disease: 1, symptom: 2, treatment: 3, disease_type: 4 }
  const counts = {}
  dataNodes.forEach(node => {
    const type = node.category || node.type
    const col = cols[type] || 0
    const cnt = counts[type] = (counts[type] || 0) + 1
    const x = 120 + col * 260
    const spacing = type === 'crop' ? 180 : 70
    const y = 80 + cnt * spacing
    pos[node.id || node.name] = { x: Math.min(x, w - 80), y: Math.min(y, h - 80) }
  })
  nodePositions.value = pos
}

function fetchFromBackend() {
  getKnowledgeGraph().then(res => {
    if (res.success && res.data) {
      nodes.value = res.data.nodes || []
      edges.value = res.data.links || []
      layoutNodes(nodes.value)
      ElMessage.success(`已加载 ${nodes.value.length} 节点，${edges.value.length} 关系`)
    }
  }).catch(() => {
    ElMessage.warning('后端图谱数据不可用，使用本地数据')
    loadLocalData()
  })
}

function loadLocalData() {
  nodes.value = [
    { id: 'crop_苹果', name: '苹果', category: 'crop', description: '蔷薇科苹果属' },
    { id: 'crop_樱桃', name: '樱桃', category: 'crop', description: '蔷薇科樱属' },
    { id: '1', name: '黑星病', category: 'disease', risk_level: '中等' },
    { id: '2', name: '雪松锈病', category: 'disease', risk_level: '中等' },
    { id: '3', name: '黑斑病', category: 'disease', risk_level: '低' },
    { id: '4', name: '白粉病', category: 'disease', risk_level: '中等' },
    { id: 's1', name: '黑色病斑', category: 'symptom' },
    { id: 's2', name: '黄色斑点', category: 'symptom' },
    { id: 's3', name: '白色粉层', category: 'symptom' },
    { id: 's4', name: '果实腐烂', category: 'symptom' },
    { id: 't1', name: '多菌灵', category: 'treatment' },
    { id: 't2', name: '代森锰锌', category: 'treatment' },
    { id: 't3', name: '腈菌唑', category: 'treatment' },
    { id: 't4', name: '石硫合剂', category: 'treatment' }
  ]
  edges.value = [
    { source: '1', target: 'crop_苹果', relation: '易患', label: 'BELONGS_TO' },
    { source: '2', target: 'crop_苹果', relation: '易患', label: 'BELONGS_TO' },
    { source: '3', target: 'crop_苹果', relation: '易患', label: 'BELONGS_TO' },
    { source: '4', target: 'crop_樱桃', relation: '易患', label: 'BELONGS_TO' },
    { source: '1', target: 's1', relation: '症状', label: 'HAS_SYMPTOM' },
    { source: '2', target: 's2', relation: '症状', label: 'HAS_SYMPTOM' },
    { source: '4', target: 's3', relation: '症状', label: 'HAS_SYMPTOM' },
    { source: '3', target: 's4', relation: '症状', label: 'HAS_SYMPTOM' },
    { source: '1', target: 't1', relation: '防治', label: 'TREATED_BY' },
    { source: '1', target: 't2', relation: '防治', label: 'TREATED_BY' },
    { source: '2', target: 't3', relation: '防治', label: 'TREATED_BY' },
    { source: '3', target: 't2', relation: '防治', label: 'TREATED_BY' },
    { source: '4', target: 't4', relation: '防治', label: 'TREATED_BY' }
  ]
  layoutNodes(nodes.value)
}

onMounted(() => {
  fetchFromBackend()
})
</script>

<style scoped>
.kg-page { display: flex; min-height: 100vh; }

.sidebar {
  width: 220px; min-height: 100vh; background: #fff;
  border-right: 1px solid #eef2f8; position: fixed;
  top: 0; left: 0; z-index: 10;
}
.logo { padding: 28px 20px; text-align: center; border-bottom: 1px solid #f0f3f9; }
.logo h2 { font-size: 16px; color: #2563eb; margin-top: 8px; }
.logo p { font-size: 12px; color: #999; margin-top: 2px; }
.nav-list { padding: 12px 8px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; cursor: pointer;
  border-left: 3px solid transparent; border-radius: 0 8px 8px 0;
  margin-bottom: 4px; color: #555;
}
.nav-item:hover { background: #f8faff; color: #2563eb; }
.nav-item.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; font-weight: 500; }
.nav-item i { font-size: 18px; width: 20px; }

.main-content {
  flex: 1; margin-left: 220px; padding: 32px;
}
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; color: #1e293b; }
.page-header p { color: #64748b; margin-top: 4px; }

.graph-layout { display: flex; gap: 20px; }
.control-panel {
  width: 240px; display: flex; flex-direction: column; gap: 16px;
  background: #fff; padding: 20px; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.filter-section h3 { font-size: 14px; color: #374151; margin-bottom: 8px; }
.type-filters { display: flex; flex-direction: column; gap: 6px; }
.stats { display: flex; gap: 16px; }
.stat { font-size: 14px; color: #64748b; }
.stat .num { font-size: 20px; font-weight: 700; color: #2563eb; }
.node-detail { padding: 12px; background: #f8fafc; border-radius: 8px; }
.node-detail h4 { font-size: 15px; color: #1e293b; margin-bottom: 4px; }
.node-detail p { font-size: 13px; color: #64748b; margin-top: 6px; }

.graph-canvas {
  flex: 1; background: #fff; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04); overflow: auto; padding: 20px;
}
.edge { stroke: #d1d5db; stroke-width: 2; transition: 0.3s; }
.edge.highlight { stroke: #2563eb; stroke-width: 3; }
.node-g { transition: 0.3s; }
.node-g:hover circle { filter: brightness(1.1); }
.node-g.selected circle { stroke: #2563eb; stroke-width: 3; }

circle { stroke: #fff; stroke-width: 2; }
.node-crop { fill: #86efac; }
.node-disease { fill: #fca5a5; }
.node-symptom { fill: #fcd34d; }
.node-treatment { fill: #93c5fd; }
.node-default { fill: #c4b5fd; }

.node-label { fill: #374151; font-weight: 500; pointer-events: none; }

.legend {
  display: flex; gap: 20px; padding: 12px 20px;
  background: #fff; border-radius: 8px; margin-top: 16px;
}
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #64748b; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.dot.crop { background: #86efac; }
.dot.disease { background: #fca5a5; }
.dot.symptom { background: #fcd34d; }
.dot.treatment { background: #93c5fd; }
</style>
