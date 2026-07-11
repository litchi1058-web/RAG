<template>
  <div class="kg-page">
    <div class="kg-header">
      <div class="header-icon">🕸️</div>
      <div class="header-text">
        <h2>知识图谱</h2>
        <p>可视化展示病害关系网络，探索病害之间的关联</p>
      </div>
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar" v-if="stats">
      <el-row :gutter="12">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-value">{{ stats.total_nodes }}</div>
            <div class="stat-label">总节点数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-value">{{ stats.total_edges }}</div>
            <div class="stat-label">总关系数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-value">{{ categoryCount }}</div>
            <div class="stat-label">节点类型数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card">
            <div class="stat-value">{{ stats.density != null ? (stats.density * 100).toFixed(2) + '%' : '-' }}</div>
            <div class="stat-label">图密度</div>
          </el-card>
        </el-col>
      </el-row>
      <div class="stats-badges" v-if="stats.category_counts">
        <el-tag
          v-for="(count, cat) in stats.category_counts"
          :key="cat"
          :type="tagType(cat)"
          size="small"
          class="stat-badge"
        >
          {{ categoryLabels[cat] || cat }}: {{ count }}
        </el-tag>
      </div>
    </div>

    <!-- Controls Bar -->
    <div class="controls-bar">
      <div class="search-area">
        <div class="search-wrapper">
          <el-input
            v-model="searchQuery"
            placeholder="搜索节点..."
            clearable
            size="small"
            class="search-input"
            :prefix-icon="SearchIcon"
            @input="onSearchInput"
            @clear="clearSearch"
          />
          <div v-if="searchResults.length > 0" class="search-dropdown">
            <div
              v-for="r in searchResults"
              :key="r.id"
              class="search-result-item"
              @click="focusNode(r.id)"
            >
              <span class="result-name">{{ r.name }}</span>
              <el-tag :type="tagType(r.category)" size="small">
                {{ categoryLabels[r.category] || r.category }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="filter-toggle">
          <el-checkbox v-model="showFilters" size="small">筛选面板</el-checkbox>
        </div>
      </div>
      <div class="mode-hint" v-if="displayMode === 'compact'">
        <el-tag size="small" type="info" effect="plain">点击病害节点展开/收起详情</el-tag>
      </div>
      <div class="controls-actions">
        <el-button-group>
          <el-button size="small" :type="displayMode === 'compact' ? 'primary' : 'default'"
            @click="displayMode !== 'compact' && toggleDisplayMode()">概览</el-button>
          <el-button size="small" :type="displayMode === 'full' ? 'primary' : 'default'"
            @click="displayMode !== 'full' && toggleDisplayMode()">全图</el-button>
        </el-button-group>
        <template v-if="displayMode === 'compact'">
          <el-button size="small" @click="expandAllDiseases">展开全部</el-button>
          <el-button size="small" @click="collapseAll">收起全部</el-button>
        </template>
        <el-button size="small" @click="refreshGraph" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button size="small" type="primary" @click="openPathDialog">查找路径</el-button>
      </div>
    </div>

    <!-- Main Area -->
    <div class="main-area">
      <!-- Left: Filter Panel -->
      <transition name="slide">
        <div v-if="showFilters" class="filter-panel">
          <div class="panel-header">
            <h4>节点类型筛选</h4>
            <el-button text size="small" @click="resetFilters">重置</el-button>
          </div>
          <div class="filter-list">
            <el-checkbox-group v-model="visibleCategories">
              <div v-for="(label, key) in categoryLabels" :key="key" class="filter-item">
                <el-checkbox :label="key" :value="key">
                  <span class="filter-label-text">{{ label }}</span>
                  <span class="filter-count">({{ categoryCounts[key] || 0 }})</span>
                </el-checkbox>
              </div>
            </el-checkbox-group>
          </div>
        </div>
      </transition>

      <!-- Center: Graph -->
      <div ref="graphContainer" class="graph-container"></div>

      <!-- Right: Node Detail Panel -->
      <transition name="slide-reverse">
        <div v-if="selectedNode" class="detail-panel">
          <div class="panel-header">
            <h4>节点详情</h4>
            <el-button text size="small" @click="selectedNode = null">&times;</el-button>
          </div>
          <div class="detail-content">
            <h3 class="node-name">{{ selectedNode.name }}</h3>
            <el-tag :type="tagType(selectedNode.category)" size="small" class="node-category-tag">
              {{ categoryLabels[selectedNode.category] || selectedNode.category }}
            </el-tag>

            <el-divider />

            <div v-if="selectedNode.detail" class="detail-field">
              <span class="field-label">详细</span>
              <p class="field-value">{{ selectedNode.detail }}</p>
            </div>
            <div v-if="selectedNode.risk_level" class="detail-field">
              <span class="field-label">风险等级</span>
              <el-tag :type="riskTagType(selectedNode.risk_level)" size="small">{{ selectedNode.risk_level }}</el-tag>
            </div>
            <div v-if="selectedNode.severity" class="detail-field">
              <span class="field-label">严重程度</span>
              <el-tag size="small">{{ selectedNode.severity }}</el-tag>
            </div>

            <el-divider />

            <div class="neighbors-section">
              <h5>关联节点 ({{ neighbors.length }})</h5>
              <div class="neighbor-list">
                <div
                  v-for="n in neighbors"
                  :key="n.id"
                  class="neighbor-item"
                  @click="focusNode(n.id)"
                >
                  <el-tag :type="tagType(n.category)" size="small" class="neighbor-tag">
                    {{ n.label }}
                  </el-tag>
                  <span class="relation-label">{{ n.relation }}</span>
                </div>
              </div>
              <div v-if="neighbors.length === 0" class="empty-hint">无关联节点</div>
            </div>

            <el-divider />

            <el-button type="primary" size="small" @click="findPathFromNode(selectedNode.id)" class="path-btn">
              查找路径
            </el-button>
            <el-button size="small" @click="goToKnowledgeDetail(selectedNode)" class="path-btn" style="margin-top: 6px;">
              📚 查看详情
            </el-button>
          </div>
        </div>
      </transition>
    </div>

    <!-- Legend Overlay -->
    <div class="legend-overlay">
      <div class="legend-title">图例</div>
      <div v-for="(color, cat) in categoryColors" :key="cat" class="legend-item">
        <span class="legend-dot" :style="{ background: color }"></span>
        <span class="legend-label">{{ categoryLabels[cat] || cat }}</span>
      </div>
    </div>

    <!-- Path Finding Dialog -->
    <el-dialog v-model="pathDialogVisible" title="查找最短路径" width="560px" :close-on-click-modal="false">
      <el-form label-width="60px">
        <el-form-item label="起点">
          <el-select
            v-model="pathSource"
            filterable
            placeholder="选择起点节点"
            style="width: 100%"
            clearable
          >
            <el-option v-for="n in allNodes" :key="n.id" :label="n.name" :value="n.id">
              <span>{{ n.name }}</span>
              <el-tag :type="tagType(n.category)" size="small" style="margin-left: 8px">
                {{ categoryLabels[n.category] || n.category }}
              </el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="终点">
          <el-select
            v-model="pathTarget"
            filterable
            placeholder="选择终点节点"
            style="width: 100%"
            clearable
          >
            <el-option v-for="n in allNodes" :key="n.id" :label="n.name" :value="n.id">
              <span>{{ n.name }}</span>
              <el-tag :type="tagType(n.category)" size="small" style="margin-left: 8px">
                {{ categoryLabels[n.category] || n.category }}
              </el-tag>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="pathResult !== null" class="path-result-area">
        <el-alert
          :title="pathResult.found ? '找到路径，共 ' + (pathResult.path.length - 1) + ' 步' : '未找到路径'"
          :type="pathResult.found ? 'success' : 'warning'"
          show-icon
          :closable="false"
        />
        <div v-if="pathResult.found" class="path-steps">
          <template v-for="(node, idx) in pathResult.path" :key="idx">
            <div class="path-step-node">
              <el-tag :type="tagType(node.category)" size="small">{{ node.name }}</el-tag>
              <span class="path-step-label" v-if="node.relation && node.relation !== 'start'">
                {{ node.relation }}
              </span>
            </div>
            <div v-if="idx < pathResult.path.length - 1" class="path-arrow">&rarr;</div>
          </template>
        </div>
      </div>
      <template #footer>
        <el-button @click="closePathDialog">关闭</el-button>
        <el-button type="primary" @click="executeFindPath" :loading="pathLoading">查找</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default { name: 'KnowledgeGraph' }
</script>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Network, DataSet } from 'vis-network/standalone'
import { knowledgeApi } from '@/api/knowledge'
import { ElMessage } from 'element-plus'
import { Search as SearchIcon, Refresh } from '@element-plus/icons-vue'

// ─── Constants ───
const categoryColors = {
  crop: '#3b82f6',
  disease: '#ef4444',
  disease_type: '#8b5cf6',
  symptom: '#10b981',
  treatment: '#f59e0b',
  cause: '#6366f1',
  prevention: '#ec4899',
  severity: '#14b8a6',
  risk_level: '#f97316',
  chemical: '#06b6d4',
}

const categoryLabels = {
  crop: '作物',
  disease: '病害',
  disease_type: '病害类型',
  symptom: '症状',
  treatment: '治疗',
  cause: '成因',
  prevention: '预防',
  severity: '严重程度',
  risk_level: '风险等级',
  chemical: '药剂',
}

// 初始只显示作物+病害，避免一开始就展示全部208个节点
const compactCategories = ['crop', 'disease']
const defaultVisibleCategories = [...compactCategories]

function tagType(cat) {
  const map = {
    crop: 'primary',
    disease: 'danger',
    disease_type: 'warning',
    symptom: 'success',
    treatment: 'warning',
    cause: 'info',
    prevention: 'danger',
    severity: 'info',
    risk_level: 'warning',
    chemical: 'primary',
  }
  return map[cat] || 'info'
}

function riskTagType(level) {
  const map = { 无: 'info', 低: 'success', 中等: 'warning', 高: 'danger' }
  return map[level] || 'info'
}

// 紧凑模式（默认）：作物+病害，层次布局
const compactOptions = {
  nodes: { shape: 'dot', size: 28, borderWidth: 2, font: { size: 14 } },
  edges: { smooth: { type: 'continuous' } },
  layout: { hierarchical: { direction: 'LR', sortMethod: 'directed', levelSeparation: 200, nodeSpacing: 150 } },
  physics: { enabled: false },
  interaction: { hover: true, tooltipDelay: 200, multiselect: false },
}

// 完整模式：全部节点，力导向布局
const fullOptions = {
  nodes: { shape: 'dot', size: 18, borderWidth: 2, font: { size: 11 } },
  edges: { smooth: { type: 'continuous' } },
  physics: {
    enabled: true,
    barnesHut: { gravitationalConstant: -4000, springLength: 150, springConstant: 0.03, damping: 0.09 },
    stabilization: { iterations: 100 },
  },
  interaction: { hover: true, tooltipDelay: 200, multiselect: false },
}

// ─── State ───
const graphContainer = ref(null)
let network = null
let nodesDataSet = null
let edgesDataSet = null

const fullNodes = ref([])
const fullEdges = ref([])
const stats = ref(null)
const loading = ref(true)

const searchQuery = ref('')
const searchResults = ref([])
let searchTimer = null

const showFilters = ref(true)
const visibleCategories = ref([...defaultVisibleCategories])

const selectedNode = ref(null)
const physicsEnabled = ref(true)
const displayMode = ref('compact') // 'compact' | 'full'
const expandedNodeIds = ref(new Set()) // 已展开的病害节点ID

const router = useRouter()
const pathDialogVisible = ref(false)
const pathSource = ref('')
const pathTarget = ref('')
const pathLoading = ref(false)
const pathResult = ref(null)

// ─── Computed ───
const categoryCount = computed(() => {
  if (!stats.value || !stats.value.category_counts) return 0
  return Object.keys(stats.value.category_counts).length
})

const categoryCounts = computed(() => {
  return stats.value?.category_counts || {}
})

const allNodes = computed(() => {
  return fullNodes.value
})

const neighbors = computed(() => {
  if (!selectedNode.value) return []
  const nodeId = selectedNode.value.id
  const result = []
  const seen = new Set()
  for (const e of fullEdges.value) {
    if (e.source === nodeId) {
      const n = fullNodes.value.find(nn => nn.id === e.target)
      if (n && !seen.has(n.id)) {
        seen.add(n.id)
        result.push({ id: n.id, label: n.name, category: n.category, relation: e.label || e.relation })
      }
    }
    if (e.target === nodeId) {
      const n = fullNodes.value.find(nn => nn.id === e.source)
      if (n && !seen.has(n.id)) {
        seen.add(n.id)
        result.push({ id: n.id, label: n.name, category: n.category, relation: e.label || e.relation })
      }
    }
  }
  return result
})

// ─── Data Formatting ───
function defaultColor(node) {
  return {
    background: categoryColors[node.category] || '#6b7280',
    border: '#fff',
    highlight: { background: '#fbbf24', border: '#fff' },
  }
}

function formatNode(n) {
  const isDisease = n.category === 'disease'
  const isExpanded = expandedNodeIds.value.has(n.id)
  const isCompact = displayMode.value === 'compact'

  // 紧凑模式下：病害节点放大 + 展开态特殊标记
  let size = 18
  if (isCompact) {
    size = isDisease ? (isExpanded ? 26 : 22) : 14
  }

  let label = n.name
  if (isCompact && isDisease && !isExpanded) {
    label = n.name.length > 12 ? n.name.slice(0, 12) + '... [+]' : n.name + ' [+]'
  }

  return {
    id: n.id,
    label: label,
    color: defaultColor(n),
    font: {
      color: '#1a1a2e',
      size: isDisease ? 13 : 11,
      strokeWidth: 2,
      strokeColor: '#ffffff',
      face: 'Arial',
    },
    size: size,
    borderWidth: isDisease ? 3 : 1,
    shape: isDisease ? 'dot' : 'dot',
    title: n.name,
  }
}

function formatEdge(e) {
  const isCompact = displayMode.value === 'compact'
  return {
    id: `${e.source}|${e.target}`,
    from: e.source,
    to: e.target,
    label: isCompact ? '' : (e.label || ''),
    arrows: isCompact ? '' : 'to',
    color: { color: '#cbd5e1', highlight: '#94a3b8' },
    font: { size: 9, color: '#64748b', strokeWidth: 0 },
    width: isCompact ? 0.8 : 1,
  }
}

// ─── Graph Rendering ───
function getExpandedNodeIds() {
  // 在紧凑模式下展开态是 Set，在完整模式下全部展开
  if (displayMode.value === 'full') {
    return new Set(fullNodes.value.filter(n => n.category === 'disease').map(n => n.id))
  }
  return expandedNodeIds.value
}

function buildVisibleNodes() {
  const catSet = new Set(visibleCategories.value)
  const expanded = getExpandedNodeIds()

  // 基础节点：符合筛选条件的 crop + disease
  const base = fullNodes.value.filter(n =>
    catSet.has(n.category) && (n.category === 'crop' || n.category === 'disease')
  )
  const baseIds = new Set(base.map(n => n.id))

  // 展开节点：已展开的病害的关联节点（不重复基础节点）
  if (expanded.size > 0) {
    const extraIds = new Set()
    for (const e of fullEdges.value) {
      const srcIsExpanded = expanded.has(e.source) && !baseIds.has(e.source)
      const tgtIsExpanded = expanded.has(e.target) && !baseIds.has(e.target)
      if (srcIsExpanded || tgtIsExpanded) {
        if (catSet.has(fullNodes.value.find(n => n.id === e.source)?.category)) extraIds.add(e.source)
        if (catSet.has(fullNodes.value.find(n => n.id === e.target)?.category)) extraIds.add(e.target)
      }
    }
    // 展开节点本身
    for (const nid of expanded) {
      const n = fullNodes.value.find(nn => nn.id === nid)
      if (n && catSet.has(n.category)) extraIds.add(nid)
    }
    const result = [...base]
    for (const nid of extraIds) {
      const n = fullNodes.value.find(nn => nn.id === nid)
      if (n && !baseIds.has(n.id)) result.push(n)
    }
    return result
  }

  return base
}

function buildVisibleEdges(visibleNodes) {
  const idSet = new Set(visibleNodes.map(n => n.id))
  return fullEdges.value.filter(e => idSet.has(e.source) && idSet.has(e.target))
}

function renderGraph() {
  if (!graphContainer.value) return

  const vNodes = buildVisibleNodes()
  const vEdges = buildVisibleEdges(vNodes)
  const visNodes = vNodes.map(formatNode)
  const visEdges = vEdges.map(formatEdge)
  const opts = displayMode.value === 'compact' ? compactOptions : fullOptions

  if (nodesDataSet && edgesDataSet) {
    nodesDataSet.clear()
    nodesDataSet.add(visNodes)
    edgesDataSet.clear()
    edgesDataSet.add(visEdges)
    // 动态切换布局
    network.setOptions(opts)
  } else {
    nodesDataSet = new DataSet(visNodes)
    edgesDataSet = new DataSet(visEdges)
    network = new Network(graphContainer.value, { nodes: nodesDataSet, edges: edgesDataSet }, opts)
    setupNetworkEvents()
  }

  if (displayMode.value === 'compact') {
    network.fit({ animation: true, padding: 30 })
  }
}

function setupNetworkEvents() {
  if (!network) return

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const nodeData = fullNodes.value.find(n => n.id === nodeId)
      if (!nodeData) return
      selectedNode.value = nodeData

      // 紧凑模式下双击展开/收起病害节点
      if (displayMode.value === 'compact' && nodeData.category === 'disease') {
        const expanded = new Set(expandedNodeIds.value)
        if (expanded.has(nodeId)) {
          expanded.delete(nodeId)
        } else {
          expanded.add(nodeId)
        }
        expandedNodeIds.value = expanded
        renderGraph()
      }
    } else {
      selectedNode.value = null
    }
  })

  network.on('doubleClick', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const nodeData = fullNodes.value.find(n => n.id === nodeId)
      if (nodeData && nodeData.category === 'disease') {
        // 双击跳转到知识详情
        goToKnowledgeDetail(nodeData)
      }
    }
  })
}

function destroyNetwork() {
  if (network) {
    network.destroy()
    network = null
    nodesDataSet = null
    edgesDataSet = null
  }
}

// ─── Data Fetching ───
async function fetchGraphData() {
  try {
    const res = await knowledgeApi.getGraph()
    const data = res.data
    if (!data || !data.nodes || data.nodes.length === 0) {
      ElMessage.warning('知识图谱为空，请先添加知识库数据')
      return false
    }
    fullNodes.value = data.nodes
    fullEdges.value = data.links
    return true
  } catch (e) {
    console.error('Failed to fetch graph data:', e)
    ElMessage.error('获取图谱数据失败')
    return false
  }
}

async function fetchStats() {
  try {
    const res = await knowledgeApi.getGraphStats()
    if (res.data && res.data.success !== false) {
      stats.value = res.data.data || res.data
    }
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

// ─── Initialization ───
onMounted(async () => {
  loading.value = true
  const ok = await fetchGraphData()
  if (ok) {
    await nextTick()
    renderGraph()
  }
  await fetchStats()
  loading.value = false
})

onBeforeUnmount(() => {
  destroyNetwork()
  if (searchTimer) clearTimeout(searchTimer)
})

// ─── Filter Logic ───
watch(visibleCategories, () => {
  selectedNode.value = null
  clearPathHighlight()
  renderGraph()
}, { deep: true })

function resetFilters() {
  visibleCategories.value = [...defaultVisibleCategories]
}

// ─── Search Logic ───
function onSearchInput() {
  clearPathHighlight()
  if (searchTimer) clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (!q) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const res = await knowledgeApi.searchGraph(q)
      searchResults.value = (res.data && (res.data.data || res.data)) || []
    } catch (e) {
      searchResults.value = []
    }
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

function focusNode(nodeId) {
  searchResults.value = []
  if (network) {
    network.selectNodes([nodeId])
    network.focus(nodeId, { scale: 1.5, animation: true })
    const nodeData = fullNodes.value.find(n => n.id === nodeId)
    if (nodeData) {
      selectedNode.value = nodeData
    }
  }
}

// ─── 模式切换 ───
function toggleDisplayMode() {
  const prev = displayMode.value
  displayMode.value = prev === 'compact' ? 'full' : 'compact'
  if (displayMode.value === 'compact') {
    // 切回紧凑模式：重置展开状态，筛选回到 crop+disease
    expandedNodeIds.value = new Set()
    visibleCategories.value = [...defaultVisibleCategories]
  } else {
    // 完整模式：显示全部类别
    visibleCategories.value = Object.keys(categoryLabels)
  }
  selectedNode.value = null
  destroyNetwork()
  nextTick(() => renderGraph())
}

function collapseAll() {
  expandedNodeIds.value = new Set()
  renderGraph()
  ElMessage.info('已全部收起')
}

function expandAllDiseases() {
  if (displayMode.value !== 'compact') return
  const allDiseaseIds = new Set(
    fullNodes.value.filter(n => n.category === 'disease').map(n => n.id)
  )
  expandedNodeIds.value = allDiseaseIds
  renderGraph()
  ElMessage.info('已全部展开')
}

// ─── Physics / View ───
function togglePhysics() {
  physicsEnabled.value = !physicsEnabled.value
  if (network) {
    network.setOptions({ physics: { enabled: physicsEnabled.value } })
  }
}

function resetView() {
  if (network) {
    network.fit({ animation: true })
    network.setOptions({ physics: { enabled: physicsEnabled.value } })
  }
}

async function refreshGraph() {
  destroyNetwork()
  loading.value = true
  const ok = await fetchGraphData()
  if (ok) {
    await nextTick()
    renderGraph()
  }
  await fetchStats()
  loading.value = false
  ElMessage.success('图谱已刷新')
}

function goToKnowledgeDetail(node) {
  if (!node || node.category !== 'disease') {
    ElMessage.info('仅病害节点有关联详情')
    return
  }
  router.push('/rag/knowledge')
}

// ─── Path Highlighting ───
let highlightedPath = null

function clearPathHighlight() {
  highlightedPath = null
  // Reset all node/edge colors by re-rendering
  if (nodesDataSet && edgesDataSet) {
    const vNodes = buildVisibleNodes()
    const vEdges = buildVisibleEdges(vNodes)
    nodesDataSet.clear()
    nodesDataSet.add(vNodes.map(formatNode))
    edgesDataSet.clear()
    edgesDataSet.add(vEdges.map(formatEdge))
  }
}

function applyPathHighlight(pathNodes) {
  highlightedPath = pathNodes
  const pathNodeIds = new Set(pathNodes.map(n => n.id))

  // Update node colors
  nodesDataSet.forEach(node => {
    if (pathNodeIds.has(node.id)) {
      nodesDataSet.update({
        id: node.id,
        color: { background: '#f59e0b', border: '#d97706', highlight: { background: '#fbbf24', border: '#d97706' } },
        size: 25,
      })
    }
  })

  // Update edge colors - find edges between consecutive path nodes
  const pathEdgeKeys = new Set()
  for (let i = 1; i < pathNodes.length; i++) {
    const from = pathNodes[i - 1].id
    const to = pathNodes[i].id
    pathEdgeKeys.add(`${from}|${to}`)
    pathEdgeKeys.add(`${to}|${from}`)
  }

  edgesDataSet.forEach(edge => {
    if (pathEdgeKeys.has(edge.id)) {
      edgesDataSet.update({
        id: edge.id,
        color: { color: '#f59e0b', highlight: '#d97706' },
        width: 3,
      })
    }
  })
}

// ─── Path Finding ───
function openPathDialog() {
  pathSource.value = ''
  pathTarget.value = ''
  pathResult.value = null
  pathDialogVisible.value = true
}

function closePathDialog() {
  pathDialogVisible.value = false
  clearPathHighlight()
}

function findPathFromNode(nodeId) {
  pathSource.value = nodeId
  pathTarget.value = ''
  pathResult.value = null
  pathDialogVisible.value = true
}

async function executeFindPath() {
  if (!pathSource.value || !pathTarget.value) {
    ElMessage.warning('请选择起点和终点')
    return
  }
  if (pathSource.value === pathTarget.value) {
    ElMessage.warning('起点和终点不能相同')
    return
  }

  pathLoading.value = true
  try {
    const res = await knowledgeApi.findPath(pathSource.value, pathTarget.value)
    const result = res.data && (res.data.data || res.data)
    if (result && result.found && result.path && result.path.length > 0) {
      pathResult.value = { found: true, path: result.path }
      clearPathHighlight()
      applyPathHighlight(result.path)
      // Fit the view to show the path nodes
      const pathIds = result.path.map(n => n.id)
      network.selectNodes(pathIds)
      network.fit({ animation: true })
    } else {
      pathResult.value = { found: false, path: [] }
    }
  } catch (e) {
    console.error('Path finding failed:', e)
    ElMessage.error('查找路径失败')
    pathResult.value = { found: false, path: [] }
  } finally {
    pathLoading.value = false
  }
}
</script>

<style scoped>
.kg-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: rgba(255,255,255,0.85);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.03);
  flex-shrink: 0;
}
.kg-header .header-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
  box-shadow: 0 6px 20px rgba(34,197,94,0.15);
}
.kg-header .header-text h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #166534 0%, #2e7d32 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.kg-header .header-text p {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.kg-page {
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f0f9ff 100%);
  padding: 24px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  position: relative;
}
.kg-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 10% 90%, rgba(46,125,50,0.08) 0%, transparent 50%),
              radial-gradient(circle at 90% 10%, rgba(26,35,126,0.06) 0%, transparent 50%);
  pointer-events: none;
}

/* ─── Stats Bar ─── */
.stats-bar {
  flex-shrink: 0;
}

.stat-card {
  text-align: center;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.04);
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  background: rgba(255,255,255,0.9);
  transition: all .3s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #166534 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.stats-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.stat-badge {
  font-weight: 500;
}

/* ─── Controls Bar ─── */
.controls-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 12px;
}

.search-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-wrapper {
  position: relative;
}

.search-input {
  width: 280px;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  max-height: 300px;
  overflow-y: auto;
  margin-top: 4px;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s;
  gap: 8px;
}

.search-result-item:hover {
  background: #f5f7fa;
}

.result-name {
  font-size: 13px;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.controls-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.mode-hint {
  flex-shrink: 0;
}

.filter-toggle {
  white-space: nowrap;
}

/* ─── Main Area ─── */
.main-area {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 0;
}

/* ─── Filter Panel ─── */
.filter-panel {
  width: 200px;
  flex-shrink: 0;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #ebeef5;
}

.panel-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

.filter-list {
  padding: 8px 14px 14px;
  overflow-y: auto;
  flex: 1;
}

.filter-item {
  padding: 4px 0;
}

.filter-label-text {
  font-size: 13px;
  color: #303133;
}

.filter-count {
  font-size: 12px;
  color: #909399;
  margin-left: 2px;
}

/* ─── Graph Container ─── */
.graph-container {
  flex: 1;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

/* ─── Detail Panel ─── */
.detail-panel {
  width: 280px;
  flex-shrink: 0;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-content {
  padding: 0 14px 14px;
  overflow-y: auto;
  flex: 1;
}

.node-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 8px 0;
  word-break: break-all;
}

.node-category-tag {
  margin-bottom: 4px;
}

.detail-field {
  margin-bottom: 8px;
}

.field-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.field-value {
  font-size: 13px;
  color: #303133;
  margin: 0;
}

.neighbors-section h5 {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}

.neighbor-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.neighbor-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: background 0.15s;
}

.neighbor-item:hover {
  background: #f5f7fa;
}

.neighbor-tag {
  flex-shrink: 0;
}

.relation-label {
  font-size: 11px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-hint {
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
  padding: 12px 0;
}

.path-btn {
  width: 100%;
}

/* ─── Legend Overlay ─── */
.legend-overlay {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: rgba(248, 250, 252, 0.98);
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  z-index: 10;
  min-width: 120px;
}

.legend-title {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  font-size: 12px;
  color: #606266;
}

/* ─── Path Dialog ─── */
.path-result-area {
  margin-top: 12px;
}

.path-steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.path-step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.path-step-label {
  font-size: 10px;
  color: #909399;
}

.path-arrow {
  font-size: 18px;
  color: #c0c4cc;
  font-weight: 700;
}

/* ─── Transitions ─── */
.slide-enter-active,
.slide-leave-active {
  transition: width 0.25s ease, opacity 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  width: 0 !important;
  opacity: 0;
  overflow: hidden;
}

.slide-reverse-enter-active,
.slide-reverse-leave-active {
  transition: width 0.25s ease, opacity 0.25s ease;
}

.slide-reverse-enter-from,
.slide-reverse-leave-to {
  width: 0 !important;
  opacity: 0;
  overflow: hidden;
}

/* ─── Utility ─── */
:deep(.el-divider--horizontal) {
  margin: 12px 0;
}
</style>
