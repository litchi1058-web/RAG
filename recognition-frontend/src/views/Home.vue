<template>
  <div class="home-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="logo">
        <el-icon :size="28" color="#2563eb"><Monitor /></el-icon>
        <h2>智能诊断</h2>
        <p>病虫害识别系统</p>
      </div>

      <div class="nav-list">
        <div class="nav-item active" @click="$router.push('/')">
          <i class="fas fa-home"></i>
          <span>病害诊断</span>
        </div>
        <div class="nav-item" @click="$router.push('/chat')">
          <i class="fas fa-robot"></i>
          <span>AI助手</span>
        </div>
        <div class="nav-item" @click="$router.push('/knowledge-graph')">
          <i class="fas fa-project-diagram"></i>
          <span>知识图谱</span>
        </div>
        <div class="nav-item" @click="$router.push('/about')">
          <i class="fas fa-info-circle"></i>
          <span>关于系统</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="status-item">
          <span class="status-dot online"></span>
          <span>系统运行中</span>
        </div>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="main-content">
      <div class="page-header">
        <h1>水果病虫害智能诊断系统</h1>
        <p>基于深度学习与RAG知识库，提供苹果、樱桃病虫害智能识别与专业防治方案</p>
      </div>

      <!-- 核心：上传区域 -->
      <div class="upload-section">
        <div class="upload-card">
          <h2>上传病害图片开始诊断</h2>

          <!-- 识别模式切换 -->
          <div class="mode-selector">
            <label>选择识别模式：</label>
            <div class="mode-buttons">
              <div
                :class="['mode-btn', { active: mode === 'quick' }]"
                @click="mode = 'quick'"
              >
                <i class="fas fa-bolt"></i>
                <span class="mode-title">快速识别</span>
                <span class="mode-desc">单模型 · 响应快</span>
                <span class="mode-acc">≈94%</span>
              </div>
              <div
                :class="['mode-btn', { active: mode === 'deep' }]"
                @click="mode = 'deep'"
              >
                <i class="fas fa-shield-alt"></i>
                <span class="mode-title">深度识别</span>
                <span class="mode-desc">多模型融合 · 最精准</span>
                <span class="mode-acc">≈95%+</span>
              </div>
            </div>
            <p class="mode-hint">
              {{ mode === 'quick' ? '轻量推理，响应迅速，适合日常快速判断' : '多模型融合决策，精度更高，适合关键场景使用' }}
            </p>
          </div>

          <!-- 上传区域 -->
          <div
            class="upload-area"
            @click="triggerUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none"
            />
            <i class="fas fa-cloud-upload-alt"></i>
            <p>点击或拖拽图片至此处上传</p>
            <span>支持 JPG / PNG / BMP，最大 16MB</span>
          </div>

          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :disabled="!selectedFile || loading"
            @click="startDiagnosis"
          >
            <i class="fas fa-search"></i>
            开始智能诊断
          </el-button>
        </div>

        <!-- 预览 -->
        <div v-if="previewUrl" class="preview-card">
          <h3>图片预览</h3>
          <img :src="previewUrl" class="preview-img" />
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-box">
        <el-icon class="loading-icon" :size="36"><Loading /></el-icon>
        <p>{{ mode === 'deep' ? '深度识别中（多模型融合分析），请稍候...' : '快速识别中，请稍候...' }}</p>
      </div>

      <!-- 诊断报告 -->
      <div v-if="result && !loading" class="report-container">
        <div class="report-header">
          <h2><i class="fas fa-file-medical-alt"></i> 病害诊断报告</h2>
          <div class="report-meta">
            <el-tag :type="result.mode === '深度识别' ? 'primary' : 'warning'" effect="dark">
              {{ result.mode || (mode === 'deep' ? '深度识别' : '快速识别') }}
            </el-tag>
            <el-tag type="success">{{ (result.confidence || 0).toFixed(1) }}% 置信度</el-tag>
          </div>
        </div>

        <!-- 基础信息 -->
        <div class="base-info">
          <div class="info-item">
            <label>病害名称</label>
            <div class="disease-name">{{ result.predicted_class || (result.prediction?.predicted_class) || '未知' }}</div>
          </div>
          <div class="info-item">
            <label>作物类型</label>
            <div>{{ result.crop || (result.prediction?.crop || '苹果/樱桃') }}</div>
          </div>
          <div class="info-item">
            <label>严重程度</label>
            <el-tag
              :type="severityTagType"
              effect="plain"
              size="large"
            >
              {{ result.severity || (result.prediction?.severity || '一般') }}
            </el-tag>
          </div>
        </div>

        <!-- Top3 预测 -->
        <div v-if="result.top3 || result.details" class="wiki-section">
          <h3 class="wiki-title">预测排行</h3>
          <div class="top3-list">
            <div
              v-for="(item, i) in (result.top3 || result.details || [])"
              :key="i"
              class="top3-item"
            >
              <span class="rank">{{ i + 1 }}</span>
              <span class="name">{{ item.class || item.predicted_class }}</span>
              <el-progress
                :percentage="parseFloat((item.confidence * 100).toFixed(1))"
                :color="i === 0 ? '#2563eb' : i === 1 ? '#8b5cf6' : '#9ca3af'"
                :stroke-width="16"
                :text-inside="true"
              />
            </div>
          </div>
        </div>

        <!-- 知识库信息 -->
        <div v-if="knowledgeInfo" class="wiki-section">
          <h3 class="wiki-title">专业诊断建议</h3>
          <div class="knowledge-card">
            <div class="kb-section" v-if="knowledgeInfo.symptoms?.length">
              <h4><i class="fas fa-stethoscope"></i> 症状特征</h4>
              <ul>
                <li v-for="(s, i) in knowledgeInfo.symptoms" :key="i">{{ s }}</li>
              </ul>
            </div>
            <div class="kb-section" v-if="knowledgeInfo.causes?.length">
              <h4><i class="fas fa-search"></i> 病因分析</h4>
              <ul>
                <li v-for="(c, i) in knowledgeInfo.causes" :key="i">{{ c }}</li>
              </ul>
            </div>
            <div class="kb-section" v-if="knowledgeInfo.treatment?.length">
              <h4><i class="fas fa-pills"></i> 治疗方案</h4>
              <ul>
                <li v-for="(t, i) in knowledgeInfo.treatment" :key="i">{{ t }}</li>
              </ul>
            </div>
            <div class="kb-section" v-if="knowledgeInfo.prevention?.length">
              <h4><i class="fas fa-shield-alt"></i> 预防措施</h4>
              <ul>
                <li v-for="(p, i) in knowledgeInfo.prevention" :key="i">{{ p }}</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- RAG 诊断报告 -->
        <div v-if="result?.ragReport" class="report-container" style="margin-top:16px">
          <div class="report-header">
            <h2><i class="fas fa-robot"></i> AI 诊断报告</h2>
            <el-tag v-if="result.ragReport.evidence_sufficient" type="success">证据充分</el-tag>
            <el-tag v-else-if="result.ragReport.low_confidence_warning" type="warning">低置信度待复核</el-tag>
          </div>
          <div class="base-info">
            <p style="line-height:1.8;white-space:pre-wrap">{{ result.ragReport.diagnostic_report || result.ragReport.summary }}</p>
          </div>
          <div v-if="result.ragReport.causes?.length" class="wiki-section">
            <h3 class="wiki-title">病因</h3>
            <ul><li v-for="(c,i) in result.ragReport.causes" :key="i">{{ c }}</li></ul>
          </div>
          <div v-if="result.ragReport.symptoms?.length" class="wiki-section">
            <h3 class="wiki-title">症状</h3>
            <ul><li v-for="(s,i) in result.ragReport.symptoms" :key="i">{{ s }}</li></ul>
          </div>
          <div v-if="result.ragReport.recommended_chemicals?.length" class="wiki-section">
            <h3 class="wiki-title">推荐药剂</h3>
            <ul><li v-for="(c,i) in result.ragReport.recommended_chemicals" :key="i">{{ typeof c === 'string' ? c : c.name }}</li></ul>
          </div>
          <div v-if="result.ragReport.prevention?.length" class="wiki-section">
            <h3 class="wiki-title">预防措施</h3>
            <ul><li v-for="(p,i) in result.ragReport.prevention" :key="i">{{ p }}</li></ul>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="report-actions">
          <el-button @click="reset" :icon="'Refresh'">重新诊断</el-button>
          <el-button type="primary" @click="$router.push('/chat')" :icon="'ChatDotSquare'">
            咨询AI助手
          </el-button>
          <el-button @click="shareResult" :icon="'Share'">分享结果</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { predictImage, getKnowledgeList, ragQuery } from '@/api'

const router = useRouter()

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const loading = ref(false)
const result = ref(null)
const mode = ref('quick')
const knowledgeInfo = ref(null)

const severityTagType = computed(() => {
  const s = result.value?.severity || result.value?.prediction?.severity || ''
  if (s.includes('严重') || s === '高') return 'danger'
  if (s.includes('中等') || s === '中') return 'warning'
  return 'success'
})

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(e) {
  const f = e.target.files[0]
  if (f) {
    selectedFile.value = f
    previewUrl.value = URL.createObjectURL(f)
  }
}

function handleDrop(e) {
  const f = e.dataTransfer.files[0]
  if (f?.type.startsWith('image/')) {
    selectedFile.value = f
    previewUrl.value = URL.createObjectURL(f)
  }
}

async function startDiagnosis() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择图片')
    return
  }

  loading.value = true
  result.value = null
  knowledgeInfo.value = null

  const fd = new FormData()
  fd.append('image', selectedFile.value)
  fd.append('mode', mode.value)

  try {
    const res = await predictImage(fd)
    if (res.success) {
      result.value = res.data || res
      ElMessage.success('诊断完成')

      // 尝试获取知识库信息
      const predictedClass = result.value.predicted_class || result.value.prediction?.predicted_class
      if (predictedClass && predictedClass !== '健康') {
        try {
          const kbRes = await getKnowledgeList()
          if (kbRes.success && kbRes.data) {
            const kb = kbRes.data
            // 匹配知识库条目
            const matchedKey = Object.keys(kb).find(key =>
              predictedClass.includes(key) || key.includes(predictedClass)
            )
            if (matchedKey) {
              knowledgeInfo.value = kb[matchedKey]
            } else {
              // 尝试按病害名模糊匹配
              for (const [key, val] of Object.entries(kb)) {
                if (val.disease_name && predictedClass.includes(val.disease_name)) {
                  knowledgeInfo.value = val
                  break
                }
              }
            }
          }
        } catch {
          // 知识库加载失败不影响诊断结果
        }

        // 获取 RAG 诊断报告
        if (predictedClass && predictedClass !== '健康') {
          try {
            const ragRes = await ragQuery(predictedClass)
            if (ragRes && ragRes.has_knowledge) {
              result.value.ragReport = ragRes
            }
          } catch {
            // RAG 报告不影响诊断结果
          }
        }
      }
    } else {
      ElMessage.error(res.message || '诊断失败')
    }
  } catch (e) {
    ElMessage.error('诊断请求失败，请确认后端服务运行中')
  } finally {
    loading.value = false
  }
}

function reset() {
  selectedFile.value = null
  previewUrl.value = ''
  result.value = null
  knowledgeInfo.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function shareResult() {
  const name = result.value?.predicted_class || result.value?.prediction?.predicted_class || '未知'
  const conf = result.value?.confidence || 0
  const text = `水果病虫害诊断结果：${name}，置信度 ${(conf * 100).toFixed(1)}%`
  navigator.clipboard?.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}
</script>

<style scoped>
.home-container {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: #fff;
  border-right: 1px solid #eef2f8;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 10;
}

.logo {
  padding: 28px 20px;
  text-align: center;
  border-bottom: 1px solid #f0f3f9;
}
.logo h2 {
  font-size: 16px;
  color: #2563eb;
  margin-top: 8px;
}
.logo p {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.nav-list {
  flex: 1;
  padding: 12px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  border-radius: 0 8px 8px 0;
  margin-bottom: 4px;
  color: #555;
  transition: all 0.2s;
}
.nav-item:hover {
  background: #f8faff;
  color: #2563eb;
}
.nav-item.active {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
  font-weight: 500;
}
.nav-item i {
  font-size: 18px;
  width: 20px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #f0f3f9;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}
.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.4);
}

/* 主内容 */
.main-content {
  flex: 1;
  margin-left: 220px;
  padding: 40px 32px;
  max-width: 1100px;
}

.page-header {
  text-align: center;
  margin-bottom: 36px;
}
.page-header h1 {
  font-size: 28px;
  color: #1e293b;
  margin-bottom: 8px;
}
.page-header p {
  font-size: 15px;
  color: #64748b;
  max-width: 650px;
  margin: 0 auto;
}

/* 上传区域 */
.upload-section {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 40px;
}
.upload-card {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.upload-card h2 {
  font-size: 18px;
  color: #1e293b;
  margin-bottom: 20px;
  text-align: center;
}

.mode-selector {
  margin-bottom: 20px;
}
.mode-selector label {
  display: block;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  margin-bottom: 10px;
  text-align: center;
}
.mode-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
}
.mode-btn {
  flex: 1;
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}
.mode-btn:hover {
  border-color: #93c5fd;
  transform: translateY(-2px);
}
.mode-btn.active {
  border-color: #2563eb;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}
.mode-btn i {
  font-size: 24px;
  margin-bottom: 8px;
  display: block;
}
.mode-btn.active i { color: #2563eb; }
.mode-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}
.mode-desc {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.mode-acc {
  display: inline-block;
  font-size: 11px;
  color: #059669;
  background: #d1fae5;
  padding: 2px 8px;
  border-radius: 10px;
}
.mode-btn.active .mode-acc {
  background: #059669;
  color: #fff;
}
.mode-hint {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 48px 20px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 24px;
  transition: 0.3s;
}
.upload-area:hover {
  border-color: #2563eb;
  background: #f8faff;
}
.upload-area i {
  font-size: 36px;
  color: #9ca3af;
  margin-bottom: 12px;
}
.upload-area p {
  font-size: 15px;
  color: #374151;
  margin-bottom: 6px;
}
.upload-area span {
  font-size: 12px;
  color: #9ca3af;
}

.submit-btn {
  width: 100%;
  font-size: 15px;
}

.preview-card {
  width: 320px;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.preview-card h3 {
  font-size: 15px;
  color: #374151;
  margin-bottom: 12px;
}
.preview-img {
  width: 100%;
  border-radius: 8px;
}

.loading-box {
  text-align: center;
  padding: 60px 0;
  color: #64748b;
}
.loading-icon {
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 诊断报告 */
.report-container {
  background: #fff;
  border-radius: 16px;
  padding: 36px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
  margin-top: 20px;
}
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 16px;
  margin-bottom: 24px;
}
.report-header h2 {
  font-size: 22px;
  color: #111827;
}
.report-meta {
  display: flex;
  gap: 12px;
}

.base-info {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}
.info-item { flex: 1; }
.info-item label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
  display: block;
}
.disease-name {
  font-size: 18px;
  font-weight: 600;
  color: #2563eb;
}

/* 百科模块 */
.wiki-section {
  margin-bottom: 28px;
}
.wiki-title {
  font-size: 17px;
  color: #111827;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

.top3-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.top3-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #f9fafb;
  border-radius: 8px;
}
.rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #374151;
  flex-shrink: 0;
}
.top3-item .name {
  min-width: 100px;
  font-size: 14px;
}
.top3-item .el-progress {
  flex: 1;
}

.knowledge-card {
  background: #f8fafc;
  padding: 20px 24px;
  border-radius: 12px;
}
.kb-section {
  margin-bottom: 20px;
}
.kb-section:last-child { margin-bottom: 0; }
.kb-section h4 {
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.kb-section ul {
  list-style: none;
  padding: 0;
}
.kb-section li {
  font-size: 14px;
  color: #4b5563;
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
}
.kb-section li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #2563eb;
}

.report-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
  margin-top: 12px;
}
</style>
