<template>
  <div class="knowledge-page">
    <div class="page-header">
      <div class="header-info">
        <h2>📚 病害知识库</h2>
        <p class="header-desc">管理和维护叶片病害知识数据，支持搜索、查看、编辑和删除操作</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="search"
          placeholder="搜索病害名称或标识..."
          style="width: 260px; margin-right: 12px;"
          clearable
          :prefix-icon="Search"
        />
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 添加病害
        </el-button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ knowledgeCount }}</div>
          <div class="stat-label">知识条目总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🍎</div>
        <div class="stat-info">
          <div class="stat-value">{{ appleCount }}</div>
          <div class="stat-label">苹果病害</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🍒</div>
        <div class="stat-info">
          <div class="stat-value">{{ cherryCount }}</div>
          <div class="stat-label">樱桃病害</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <div class="stat-value">{{ highRiskCount }}</div>
          <div class="stat-label">高风险病害</div>
        </div>
      </div>
    </div>

    <div class="knowledge-grid">
      <div 
        v-for="item in pagedKnowledge" 
        :key="item[0]" 
        class="knowledge-card"
        @click="viewDetail(item[0])"
      >
        <div class="card-header">
          <div class="card-tags">
            <el-tag :type="getCropType(item[1].crop_type)" size="small">{{ item[1].crop_type }}</el-tag>
            <el-tag :type="getRiskType(item[1].risk_level)" size="small">{{ item[1].risk_level || '未知' }}</el-tag>
          </div>
          <div class="card-actions">
            <el-button 
              size="small" 
              @click.stop="openDialog(item[0])"
              icon="Edit"
              circle
            />
            <el-button 
              size="small" 
              type="danger"
              @click.stop="handleDelete(item[0])"
              icon="Delete"
              circle
            />
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-title">{{ item[1].disease_name }}</h3>
          <p class="card-summary">{{ item[1].diagnosis_summary?.slice(0, 100) || item[1].severity?.slice(0, 80) }}...</p>
          <div class="card-meta">
            <span class="meta-item">
              <el-icon :size="14"><WarningFilled /></el-icon>
              {{ getDiseaseType(item[1]) }}
            </span>
            <span class="meta-item">
              <el-icon :size="14"><Tickets /></el-icon>
              {{ item[1].symptoms?.length || 0 }} 症状
            </span>
            <span class="meta-item">
              <el-icon :size="14"><Guide /></el-icon>
              {{ item[1].recommended_chemicals?.length || 0 }} 药剂
            </span>
          </div>
        </div>
        <div class="card-footer">
          <span class="card-key">{{ item[0] }}</span>
          <span class="card-action">查看详情 →</span>
        </div>
      </div>

      <div v-if="pagedKnowledge.length === 0 && filteredKnowledge.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>暂无知识数据</h3>
        <p>后端 COMPLETE_KNOWLEDGE_BASE 已预置 {{ knowledgeCount }} 条知识数据</p>
      </div>
    </div>

    <div v-if="totalPages > 1" class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredKnowledge.length"
        layout="prev, pager, next, total"
        background
      />
    </div>

    <el-dialog v-model="detailDialogVisible" title="病害详情" width="800px" top="5vh">
      <div v-if="detailData" class="detail-content">
        <div class="detail-header">
          <div class="detail-title">
            <el-icon :size="24" color="#409eff"><Document /></el-icon>
            <span>{{ detailData.disease_name }}</span>
          </div>
          <div class="detail-tags">
            <el-tag :type="getCropType(detailData.crop_type)" size="small">{{ detailData.crop_type }}</el-tag>
            <el-tag :type="getRiskType(detailData.risk_level)" size="small">{{ detailData.risk_level }}风险</el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">📋 病情概述</h4>
          <p class="section-content">{{ detailData.diagnosis_summary || detailData.summary || '暂无概述' }}</p>
        </div>

        <div class="detail-section">
          <h4 class="section-title">⚠️ 严重程度</h4>
          <p class="section-content">{{ detailData.severity || '未知' }}</p>
        </div>

        <div class="detail-section">
          <h4 class="section-title">📝 症状表现</h4>
          <ul class="section-list">
            <li v-for="(s, i) in detailData.symptoms" :key="i">{{ i + 1 }}. {{ s }}</li>
          </ul>
        </div>

        <div class="detail-section">
          <h4 class="section-title">🔍 发病原因</h4>
          <ul class="section-list">
            <li v-for="(c, i) in detailData.causes" :key="i">{{ i + 1 }}. {{ c }}</li>
          </ul>
        </div>

        <div v-if="detailData.recommended_chemicals?.length" class="detail-section">
          <h4 class="section-title">💊 推荐药剂</h4>
          <div class="chemicals-grid">
            <div v-for="(chem, i) in detailData.recommended_chemicals" :key="i" class="chemical-card">
              <div class="chem-name">{{ chem.name }}</div>
              <div class="chem-info">
                <span>类型：{{ chem.type }}</span>
                <span>稀释：{{ chem.dilution }}</span>
                <span v-if="chem.safe_interval">安全间隔：{{ chem.safe_interval }}天</span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">✅ 防治方案</h4>
          <ul class="section-list">
            <li v-for="(t, i) in detailData.treatment_plan || detailData.treatment" :key="i">{{ i + 1 }}. {{ t }}</li>
          </ul>
        </div>

        <div class="detail-section">
          <h4 class="section-title">🛡️ 预防措施</h4>
          <ul class="section-list">
            <li v-for="(p, i) in detailData.prevention" :key="i">{{ i + 1 }}. {{ p }}</li>
          </ul>
        </div>

        <div v-if="detailData.precautions?.length" class="detail-section warning-section">
          <h4 class="section-title">🚨 注意事项</h4>
          <ul class="section-list">
            <li v-for="(p, i) in detailData.precautions" :key="i">{{ i + 1 }}. {{ p }}</li>
          </ul>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editingKey ? '编辑病害' : '添加病害'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="病害标识">
          <el-input v-model="form.disease_key" :disabled="!!editingKey" />
        </el-form-item>
        <el-form-item label="病害名称">
          <el-input v-model="form.disease_name" />
        </el-form-item>
        <el-form-item label="作物类型">
          <el-input v-model="form.crop_type" placeholder="例如：苹果、樱桃、梨..." />
        </el-form-item>
        <el-form-item label="病害类型">
          <el-input v-model="form.disease_type" placeholder="例如：黑星病、白粉病、健康..." />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="form.risk_level" style="width: 100%;">
            <el-option v-for="l in riskLevels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="症状">
          <el-input v-model="form.symptomsText" type="textarea" :rows="3" placeholder="每行一个症状" />
        </el-form-item>
        <el-form-item label="病因">
          <el-input v-model="form.causesText" type="textarea" :rows="3" placeholder="每行一个病因" />
        </el-form-item>
        <el-form-item label="治疗方法">
          <el-input v-model="form.treatmentText" type="textarea" :rows="3" placeholder="每行一个方法" />
        </el-form-item>
        <el-form-item label="预防措施">
          <el-input v-model="form.preventionText" type="textarea" :rows="3" placeholder="每行一个措施" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default { name: 'Knowledge' }
</script>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '@/api/knowledge'
import { Search, Plus, Document, Edit, Delete, WarningFilled, Tickets, Guide } from '@element-plus/icons-vue'

const search = ref('')
const knowledge = ref({})
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const editingKey = ref(null)
const form = ref({})
const detailData = ref(null)

const riskLevels = ['无', '低', '中等', '高']

const currentPage = ref(1)
const pageSize = ref(8)

const filteredKnowledge = computed(() => {
  const entries = Object.entries(knowledge.value)
  if (!search.value) return entries
  const s = search.value.toLowerCase()
  return entries.filter(([k, v]) =>
    k.toLowerCase().includes(s) ||
    v.disease_name?.toLowerCase().includes(s) ||
    v.crop_type?.toLowerCase().includes(s)
  )
})

const totalPages = computed(() => Math.ceil(filteredKnowledge.value.length / pageSize.value))

const pagedKnowledge = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredKnowledge.value.slice(start, start + pageSize.value)
})

// Reset pagination when search changes
watch(search, () => { currentPage.value = 1 })

const knowledgeCount = computed(() => Object.keys(knowledge.value).length)

const appleCount = computed(() => {
  return Object.values(knowledge.value).filter(k => k.crop_type === '苹果').length
})

const cherryCount = computed(() => {
  return Object.values(knowledge.value).filter(k => k.crop_type === '樱桃').length
})

const highRiskCount = computed(() => {
  return Object.values(knowledge.value).filter(k => k.risk_level === '高').length
})

const getRiskType = (level) => ({
  '无': 'success', '低': 'info', '中等': 'warning', '高': 'danger'
}[level] || '')

const getCropType = (crop) => ({
  '苹果': 'success', '樱桃': 'warning'
}[crop] || 'info')

const getDiseaseType = (item) => {
  const name = item.disease_name || ''
  if (name.includes('健康')) return '健康'
  
  const diseaseNames = ['黑星病', '黑斑病', '白粉病', '锈病', '雪松锈病']
  for (const dn of diseaseNames) {
    if (name.includes(dn)) return dn
  }
  
  return item.disease_type || '未知'
}

const loadData = async () => {
  const res = await knowledgeApi.list()
  knowledge.value = res.data || res
  currentPage.value = 1
}

const viewDetail = async (key) => {
  const res = await knowledgeApi.get(key)
  detailData.value = res.data || res
  detailDialogVisible.value = true
}

const openDialog = async (key) => {
  if (key) {
    editingKey.value = key
    const res = await knowledgeApi.get(key)
    const item = res.data || res
    form.value = {
      disease_key: key,
      disease_name: item.disease_name,
      crop_type: item.crop_type,
      disease_type: item.disease_type,
      risk_level: item.risk_level,
      symptomsText: (item.symptoms || []).join('\n'),
      causesText: (item.causes || []).join('\n'),
      treatmentText: ((item.treatment || item.treatment_plan) || []).join('\n'),
      preventionText: (item.prevention || []).join('\n')
    }
  } else {
    editingKey.value = null
    form.value = {
      disease_key: '', disease_name: '', crop_type: '',
      disease_type: '', risk_level: '中等',
      symptomsText: '', causesText: '', treatmentText: '', preventionText: ''
    }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  const data = {
    ...form.value,
    symptoms: form.value.symptomsText.split('\n').filter(s => s.trim()),
    causes: form.value.causesText.split('\n').filter(s => s.trim()),
    treatment_plan: form.value.treatmentText.split('\n').filter(s => s.trim()),
    prevention: form.value.preventionText.split('\n').filter(s => s.trim())
  }

  if (editingKey.value) {
    await knowledgeApi.update(editingKey.value, data)
    ElMessage.success('更新成功')
  } else {
    await knowledgeApi.create(data)
    ElMessage.success('添加成功')
  }
  dialogVisible.value = false
  loadData()
}

const handleDelete = async (key) => {
  await ElMessageBox.confirm(`确定要删除 "${key}" 吗？`, '确认', { type: 'warning' })
  await knowledgeApi.remove(key)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.knowledge-page {
  padding: 32px;
  width: 100%;
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f0f9ff 100%);
  position: relative;
}
.knowledge-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 10% 90%, rgba(46,125,50,0.1) 0%, transparent 50%),
              radial-gradient(circle at 90% 10%, rgba(26,35,126,0.08) 0%, transparent 50%);
  pointer-events: none;
}
.knowledge-page::after {
  content: '';
  position: absolute;
  bottom: -200px;
  right: -200px;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(46,125,50,0.06) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: bg-float 12s ease-in-out infinite;
}
@keyframes bg-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-30px, -30px) scale(1.1); }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(255,255,255,0.8);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.03);
}

.header-info h2 {
  font-size: 28px;
  font-weight: 800;
  color: #1f2937;
  margin: 0 0 8px;
  background: linear-gradient(135deg, #166534 0%, #2e7d32 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
}
.header-actions .el-input {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: all .3s;
}
.header-actions .el-input:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.header-actions .el-input__inner {
  border-radius: 12px;
  padding: 12px 16px;
}
.header-actions .el-button {
  border-radius: 12px;
  padding: 10px 24px;
  font-weight: 600;
}
.header-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(46,125,50,0.3);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 36px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(145deg, #ffffff 0%, #fafafa 100%);
  padding: 28px;
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0,0,0,0.04);
  transition: all .4s cubic-bezier(0.4,0,0.2,1);
  animation: card-appear 0.6s ease-out forwards;
  opacity: 0;
}
.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }
.stat-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
}
@keyframes card-appear {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
  box-shadow: 0 8px 24px rgba(34,197,94,0.18);
  transition: all .3s;
}
.stat-card:hover .stat-icon {
  transform: scale(1.1);
}
.stat-card:nth-child(2) .stat-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fef9c3 100%);
  box-shadow: 0 8px 24px rgba(251,191,36,0.18);
}
.stat-card:nth-child(3) .stat-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #eef2ff 100%);
  box-shadow: 0 8px 24px rgba(99,102,241,0.18);
}
.stat-card:nth-child(4) .stat-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
  box-shadow: 0 8px 24px rgba(239,68,68,0.18);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #166534 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

.stat-label {
  font-size: 15px;
  color: #6b7280;
  font-weight: 500;
  margin-top: 4px;
}

.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}

.knowledge-card {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  overflow: hidden;
  cursor: pointer;
  transition: all .4s cubic-bezier(0.4,0,0.2,1);
  animation: card-enter 0.5s ease-out forwards;
  opacity: 0;
}
.knowledge-card:nth-child(odd) { animation-delay: 0.05s; }
.knowledge-card:nth-child(even) { animation-delay: 0.1s; }
.knowledge-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(46,125,50,0.12);
  border-color: rgba(46,125,50,0.15);
}
@keyframes card-enter {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-bottom: 1px solid rgba(46,125,50,0.08);
}

.card-tags {
  display: flex;
  gap: 8px;
}

.card-actions {
  display: flex;
  gap: 8px;
}
.card-actions .el-button {
  opacity: 0;
  transition: opacity .2s;
}
.knowledge-card:hover .card-actions .el-button {
  opacity: 1;
}

.card-body {
  padding: 20px;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px;
  line-height: 1.3;
}

.card-summary {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: #f9fafb;
  border-top: 1px solid rgba(0,0,0,0.04);
}

.card-key {
  font-size: 12px;
  color: #9ca3af;
  font-family: monospace;
}

.card-action {
  font-size: 13px;
  color: #22c55e;
  font-weight: 500;
  transition: color .2s;
}
.knowledge-card:hover .card-action {
  color: #16a34a;
}

.count-badge {
  display: inline-block;
  min-width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
  color: #166534;
  font-size: 12px;
  font-weight: 600;
  border-radius: 12px;
  padding: 0 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  animation: icon-bounce 2s ease-in-out infinite;
}
@keyframes icon-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px;
}

.empty-state p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.detail-content {
  max-height: 65vh;
  overflow-y: auto;
  padding-right: 8px;
}
.detail-content::-webkit-scrollbar {
  width: 6px;
}
.detail-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}
.detail-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.detail-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-radius: 16px;
  margin-bottom: 24px;
  border: 1px solid rgba(46,125,50,0.1);
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}

.detail-tags {
  display: flex;
  gap: 10px;
}

.detail-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafafa;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,0.04);
  transition: all .3s;
}
.detail-section:hover {
  background: #ffffff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-content {
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
  text-indent: 2em;
  margin: 0;
}

.section-list {
  margin: 0;
  padding-left: 24px;
}

.section-list li {
  font-size: 14px;
  line-height: 1.9;
  color: #4b5563;
  margin-bottom: 10px;
  position: relative;
  padding-left: 12px;
}
.section-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-radius: 50%;
}

.section-list li:last-child {
  margin-bottom: 0;
}

.warning-section {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  padding: 20px;
  border-radius: 16px;
  border: 1px solid rgba(239,68,68,0.2);
}

.warning-section .section-title {
  color: #dc2626;
}

.warning-section .section-list li::before {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.chemicals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chemical-card {
  background: linear-gradient(145deg, #ffffff 0%, #f0fdf4 100%);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(46,125,50,0.1);
  transition: all .3s;
}
.chemical-card:hover {
  box-shadow: 0 4px 16px rgba(46,125,50,0.1);
}

.chem-name {
  font-size: 15px;
  font-weight: 600;
  color: #166534;
  margin-bottom: 10px;
}

.chem-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chem-info span {
  font-size: 13px;
  color: #6b7280;
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 20px 0 12px;
}

.pagination-bar :deep(.el-pagination) {
  .el-pager li {
    border-radius: 8px;
    margin: 0 4px;
    min-width: 36px;
    height: 36px;
    line-height: 36px;
  }
  .el-pager li.is-active {
    background: linear-gradient(135deg, #166534 0%, #22c55e 100%);
    border-radius: 8px;
  }
}
</style>