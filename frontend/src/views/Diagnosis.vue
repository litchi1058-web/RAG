<template>
  <div class="diagnosis-page">
    <div class="page-header">
      <div class="header-info">
        <h2>📋 识别记录</h2>
        <p class="header-desc">查看历史病害诊断记录，支持按时间浏览与删除</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ total }}</div>
          <div class="stat-label">总记录数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔴</div>
        <div class="stat-info">
          <div class="stat-value">{{ highRiskCount }}</div>
          <div class="stat-label">高风险记录</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🟡</div>
        <div class="stat-info">
          <div class="stat-value">{{ mediumRiskCount }}</div>
          <div class="stat-label">中风险记录</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🟢</div>
        <div class="stat-info">
          <div class="stat-value">{{ lowRiskCount }}</div>
          <div class="stat-label">低风险记录</div>
        </div>
      </div>
    </div>

    <div class="table-card">
      <el-table :data="list" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="disease_name" label="病害名称" min-width="160" />
        <el-table-column label="置信度" width="140">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round((row.confidence || 0) * 100)"
              :color="confidenceColor(row.confidence)"
              :stroke-width="10"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="110">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small" effect="light">
              {{ row.risk_level || '未知' }}风险
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="识别时间" width="180">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" plain @click="handleDelete(row.id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-state">
            <div class="empty-icon">🌱</div>
            <h3>暂无识别记录</h3>
            <p>进行病害识别后，记录将显示在这里</p>
          </div>
        </template>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="page"
          :page-size="limit"
          :total="total"
          @current-change="loadData"
          layout="prev, pager, next, total"
          background
        />
      </div>
    </div>
  </div>
</template>

<script>
export default { name: 'Diagnosis' }
</script>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { diagnosisApi } from '@/api/diagnosis'

const list = ref([])
const page = ref(1)
const limit = 20
const total = ref(0)
const loading = ref(false)

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const riskTagType = (level) => {
  const map = { '无': 'info', '低': 'success', '中等': 'warning', '中高': 'warning', '高': 'danger', '极高': 'danger' }
  return map[level] || 'info'
}

const confidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#22c55e'
  if (confidence >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

const highRiskCount = computed(() => list.value.filter(r => ['高', '极高'].includes(r.risk_level)).length)
const mediumRiskCount = computed(() => list.value.filter(r => ['中等', '中高'].includes(r.risk_level)).length)
const lowRiskCount = computed(() => list.value.filter(r => ['低', '无'].includes(r.risk_level)).length)

const loadData = async () => {
  loading.value = true
  try {
    const res = await diagnosisApi.history(page.value, limit)
    list.value = res.data || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('加载记录失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  await ElMessageBox.confirm('确定要删除这条记录吗？', '确认', { type: 'warning' })
  await diagnosisApi.remove(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.diagnosis-page {
  padding: 32px;
  width: 100%;
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #f0f9ff 100%);
  position: relative;
}
.diagnosis-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 10% 90%, rgba(46,125,50,0.1) 0%, transparent 50%),
              radial-gradient(circle at 90% 10%, rgba(26,35,126,0.08) 0%, transparent 50%);
  pointer-events: none;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding: 24px;
  background: rgba(255,255,255,0.85);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.03);
}
.header-info h2 {
  font-size: 28px;
  font-weight: 800;
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(145deg, #ffffff 0%, #fafafa 100%);
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
  transition: all .3s;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
  box-shadow: 0 6px 20px rgba(34,197,94,0.15);
}
.stat-card:nth-child(2) .stat-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
  box-shadow: 0 6px 20px rgba(239,68,68,0.15);
}
.stat-card:nth-child(3) .stat-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fef9c3 100%);
  box-shadow: 0 6px 20px rgba(251,191,36,0.15);
}
.stat-card:nth-child(4) .stat-icon {
  background: linear-gradient(135deg, #dcfce7 0%, #d1fae5 100%);
  box-shadow: 0 6px 20px rgba(34,197,94,0.15);
}
.stat-info { flex: 1; }
.stat-value {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #166534 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
}

.table-card {
  background: rgba(255,255,255,0.9);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.04);
}
.table-card :deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}
.table-card :deep(.el-table th) {
  background: rgba(240,253,244,0.8);
  border-bottom: 2px solid rgba(46,125,50,0.15);
  color: #1f2937;
  font-weight: 600;
  font-size: 14px;
  padding: 14px 12px;
}
.table-card :deep(.el-table td) {
  border-bottom: 1px solid rgba(0,0,0,0.03);
  padding: 14px 12px;
  font-size: 14px;
}
.table-card :deep(.el-table tr:hover > td) {
  background: rgba(46,125,50,0.04);
}
.time-cell {
  color: #6b7280;
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}
.empty-state p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.pagination-bar {
  display: flex;
  justify-content: center;
  padding: 20px 0 8px;
}
.pagination-bar :deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, #166534 0%, #22c55e 100%);
}

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .page-header { flex-direction: column; gap: 16px; }
}
</style>
