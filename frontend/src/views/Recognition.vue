<template>
  <div class="recognition-page">
    <div class="page-header">
      <h2>🌿 叶片病害识别</h2>
      <p class="page-subtitle">上传叶片图像，AI智能识别病害并生成诊断报告</p>
    </div>

    <el-dialog
      v-model="downloadDialogVisible"
      title="选择下载格式"
      width="360px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div class="download-options">
        <div class="download-option" @click="downloadAs('pdf')">
          <div class="option-icon pdf-icon">📄</div>
          <div class="option-content">
            <div class="option-title">PDF 格式</div>
            <div class="option-desc">适合打印和存档，保留完整格式</div>
          </div>
        </div>
        <div class="download-option" @click="downloadAs('png')">
          <div class="option-icon png-icon">🖼️</div>
          <div class="option-content">
            <div class="option-title">PNG 图片</div>
            <div class="option-desc">适合分享到社交媒体或嵌入文档</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="downloadDialogVisible = false">取消</el-button>
      </template>
    </el-dialog>

    <div class="page-content">
      <el-card shadow="hover" class="upload-card">
        <div class="card-header">
          <div class="header-icon">📷</div>
          <div class="header-text">
            <h3>上传叶片图像</h3>
            <p>支持 JPG / PNG / WEBP 格式，单张不超过 10MB</p>
          </div>
        </div>

        <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="hidden-input"
            @change="handleFileChange"
          />
          
          <div v-if="!previewUrl" class="upload-placeholder">
            <div class="placeholder-icon">
              <el-icon :size="56" color="#409eff"><UploadFilled /></el-icon>
            </div>
            <div class="placeholder-content">
              <p class="placeholder-title">点击或拖拽上传图像</p>
              <p class="placeholder-hint">请上传清晰的叶片正面图像，便于准确识别</p>
            </div>
          </div>
          
          <div v-else class="preview-container">
            <div class="preview-image-wrapper">
              <el-image :src="previewUrl" fit="contain" class="preview-image" />
              <div class="image-overlay">
                <el-button size="small" type="primary" round @click.stop="resetUpload">
                  <el-icon><Refresh /></el-icon> 重新选择
                </el-button>
              </div>
            </div>
            <div class="preview-info">
              <el-tag type="info" size="small">{{ selectedFile?.name }}</el-tag>
              <span class="file-size">{{ formatFileSize(selectedFile?.size) }}</span>
            </div>
          </div>
        </div>

        <div class="action-area">
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedFile || predicting"
            :loading="predicting"
            @click="predict"
            class="predict-btn"
          >
            <el-icon><Search /></el-icon>
            {{ predicting ? 'AI识别中...' : '开始智能识别' }}
          </el-button>
        </div>
      </el-card>

      <el-card shadow="hover" class="result-card" v-if="prediction || diagnosing || diagnosisResult">
        <div class="card-header">
          <div class="header-icon">🔍</div>
          <div class="header-text">
            <h3>识别结果</h3>
            <el-tag v-if="prediction" :type="confidenceLevel" size="small">
              置信度 {{ (prediction.confidence * 100).toFixed(1) }}%
            </el-tag>
          </div>
        </div>

        <div v-if="predicting && !prediction" class="loading-state">
          <el-icon :size="48" color="#409eff" class="loading-icon"><Loading /></el-icon>
          <p class="loading-text">AI 模型正在分析叶片图像...</p>
          <p class="loading-hint">请稍候，识别过程可能需要几秒钟</p>
        </div>

        <div v-if="prediction && !diagnosing && !diagnosisResult" class="recognition-result">
          <div class="result-header">
            <div class="disease-title">
              <el-icon :size="20" color="#f56c6c"><Warning /></el-icon>
              <span>{{ prediction.disease_name }}</span>
            </div>
            <el-tag :type="riskTagType(prediction.risk_level)" size="medium">
              {{ prediction.risk_level }}风险
            </el-tag>
          </div>

          <div class="confidence-bar">
            <div class="bar-label">识别置信度</div>
            <div class="bar-container">
              <el-progress
                :percentage="Math.round(prediction.confidence * 100)"
                :color="confidenceColors"
                :stroke-width="14"
                :text-inside="true"
                class="confidence-progress"
              />
            </div>
            <div class="confidence-hint" :class="confidenceLevel">
              {{ prediction.confidence >= 0.8 ? '识别结果高度可靠' : prediction.confidence >= 0.5 ? '识别结果基本可靠' : '建议结合症状进一步确认' }}
            </div>
          </div>

          <div v-if="prediction.symptoms && prediction.symptoms.length" class="symptoms-box">
            <div class="box-title">
              <el-icon color="#f56c6c"><CircleClose /></el-icon>
              <span>典型症状</span>
            </div>
            <div class="symptoms-tags">
              <el-tag
                v-for="(s, i) in prediction.symptoms"
                :key="i"
                type="danger"
                size="small"
                effect="plain"
                class="symptom-tag"
              >
                {{ s }}
              </el-tag>
            </div>
          </div>

          <div class="action-divider">
            <span></span>
            <span class="divider-text">下一步</span>
            <span></span>
          </div>

          <el-button
            type="primary"
            size="large"
            @click="fetchDiagnosis"
            :loading="diagnosing"
            :disabled="diagnosing"
            class="diagnosis-btn"
          >
            <el-icon><Document /></el-icon>
            生成诊断报告
          </el-button>
        </div>

        <div v-if="diagnosisResult" class="diagnosis-report" ref="reportRef">
          <div class="report-header">
            <div class="report-title">
              <el-icon color="#67c23a"><Check /></el-icon>
              <span>诊断报告</span>
            </div>
            <div class="report-meta">
              <span class="meta-item">📅 {{ formatDate(new Date()) }}</span>
              <span class="meta-item">🆔 #{{ generateReportId() }}</span>
            </div>
          </div>

          <div class="report-overview">
            <div class="overview-card">
              <div class="overview-icon" :class="severityTagType(diagnosisResult.severity || '')">
                {{ diagnosisResult.severity?.includes('严重') || diagnosisResult.severity?.includes('爆发') ? '⚠️' : diagnosisResult.severity?.includes('中度') ? '⚡' : '✅' }}
              </div>
              <div class="overview-content">
                <div class="overview-label">病情严重程度</div>
                <div class="overview-value">{{ diagnosisResult.severity || '未知' }}</div>
              </div>
            </div>
            <div class="overview-card">
              <div class="overview-icon" :class="riskTagType(diagnosisResult.risk_level || '')">
                🎯
              </div>
              <div class="overview-content">
                <div class="overview-label">风险等级</div>
                <div class="overview-value">{{ diagnosisResult.risk_level || '未知' }}</div>
              </div>
            </div>
            <div class="overview-card">
              <div class="overview-icon info">📊</div>
              <div class="overview-content">
                <div class="overview-label">识别置信度</div>
                <div class="overview-value">{{ (prediction?.confidence * 100).toFixed(1) }}%</div>
              </div>
            </div>
          </div>

          <div v-if="diagnosisResult.summary" class="summary-section">
            <div class="section-title">
              <el-icon color="#409eff"><InfoFilled /></el-icon>
              <span>病情概述</span>
            </div>
            <div class="summary-content">
              {{ diagnosisResult.summary }}
            </div>
          </div>

          <div class="report-sections">
            <div class="report-section" v-if="diagnosisResult.symptoms?.length">
              <div class="section-header">
                <div class="section-icon symptoms-icon">📝</div>
                <span class="section-title">详细症状描述</span>
              </div>
              <div class="section-content">
                <div v-for="(s, i) in diagnosisResult.symptoms" :key="i" class="symptom-item">
                  <span class="item-number">{{ i + 1 }}.</span>
                  <span>{{ s }}</span>
                </div>
              </div>
            </div>

            <div class="report-section" v-if="diagnosisResult.causes?.length">
              <div class="section-header">
                <div class="section-icon causes-icon">🔍</div>
                <span class="section-title">发病原因分析</span>
              </div>
              <div class="section-content">
                <div v-for="(c, i) in diagnosisResult.causes" :key="i" class="cause-item">
                  <el-icon color="#e6a23c"><Warning /></el-icon>
                  <span>{{ c }}</span>
                </div>
              </div>
            </div>

            <div class="report-section" v-if="diagnosisResult.recommended_chemicals?.length">
              <div class="section-header">
                <div class="section-icon chemicals-icon">💊</div>
                <span class="section-title">推荐药剂</span>
              </div>
              <div class="section-content">
                <div class="chemicals-grid">
                  <div v-for="(chem, i) in diagnosisResult.recommended_chemicals" :key="i" class="chemical-card">
                    <div class="chem-header">
                      <span class="chem-name">{{ chem.name }}</span>
                      <el-tag :type="chemTypeTag(chem.type)" size="small">{{ chem.type }}</el-tag>
                    </div>
                    <div class="chem-body">
                      <div class="chem-row">
                        <span class="row-icon">📐</span>
                        <span>稀释倍数：{{ chem.dilution }}</span>
                      </div>
                      <div v-if="chem.safe_interval" class="chem-row safety">
                        <span class="row-icon">⏱️</span>
                        <span>安全间隔期：{{ chem.safe_interval }}天</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="report-section" v-if="diagnosisResult.treatment_plan?.length">
              <div class="section-header">
                <div class="section-icon treatment-icon">✅</div>
                <span class="section-title">防治方案</span>
              </div>
              <div class="section-content">
                <div v-for="(t, i) in diagnosisResult.treatment_plan" :key="i" class="treatment-item">
                  <span class="item-check">✓</span>
                  <span>{{ t }}</span>
                </div>
              </div>
            </div>

            <div class="report-section" v-if="diagnosisResult.prevention?.length">
              <div class="section-header">
                <div class="section-icon prevention-icon">🛡️</div>
                <span class="section-title">预防措施</span>
              </div>
              <div class="section-content">
                <div v-for="(p, i) in diagnosisResult.prevention" :key="i" class="prevention-item">
                  <el-icon color="#409eff"><Lock /></el-icon>
                  <span>{{ p }}</span>
                </div>
              </div>
            </div>

            <div class="report-section precautions-section" v-if="diagnosisResult.precautions?.length">
              <div class="section-header">
                <div class="section-icon precautions-icon">⚠️</div>
                <span class="section-title">注意事项</span>
              </div>
              <div class="section-content">
                <div v-for="(p, i) in diagnosisResult.precautions" :key="i" class="precaution-item">
                  <el-icon color="#f56c6c"><WarningFilled /></el-icon>
                  <span>{{ p }}</span>
                </div>
              </div>
            </div>

            <div class="report-section" v-if="diagnosisResult.related_diseases?.length">
              <div class="section-header">
                <div class="section-icon related-icon">🔗</div>
                <span class="section-title">相关病害</span>
              </div>
              <div class="section-content">
                <div class="related-tags">
                  <el-tag
                    v-for="(rd, i) in diagnosisResult.related_diseases"
                    :key="i"
                    type="info"
                    size="small"
                    effect="plain"
                    @click="quickQuery(rd)"
                  >
                    <el-icon><Link /></el-icon> {{ rd }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <div class="report-footer" ref="reportFooterRef">
            <el-button type="primary" @click="resetUpload">
              <el-icon><Refresh /></el-icon> 识别新图像
            </el-button>
            <el-button @click="downloadReport">
              <el-icon><Download /></el-icon> 下载报告
            </el-button>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="empty-card" v-else>
        <div class="empty-state">
          <div class="empty-icon">🌱</div>
          <h3>等待上传图像</h3>
          <p>请在上方上传叶片图像，AI将自动识别病害并生成诊断报告</p>
        </div>
      </el-card>
    </div>

    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="error"
      show-icon
      closable
      class="error-alert"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { modelApi } from '@/api/model'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import {
  UploadFilled, Refresh, Search, Loading, Document, Warning,
  CircleClose, Check, Lock, WarningFilled,
  InfoFilled, Link, Download
} from '@element-plus/icons-vue'

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const predicting = ref(false)
const prediction = ref(null)
const errorMsg = ref('')
const diagnosing = ref(false)
const diagnosisResult = ref(null)
const activeReportPanels = ref(['symptoms', 'treatment'])
const reportRef = ref(null)
const reportFooterRef = ref(null)
const downloadDialogVisible = ref(false)

const confidenceLevel = computed(() => {
  if (!prediction.value) return 'info'
  const pct = prediction.value.confidence
  if (pct >= 0.8) return 'success'
  if (pct >= 0.5) return 'warning'
  return 'danger'
})

const confidenceColors = computed(() => {
  if (!prediction.value) return []
  const pct = prediction.value.confidence
  if (pct >= 0.8) return ['#67c23a']
  if (pct >= 0.5) return ['#e6a23c']
  return ['#f56c6c']
})

function riskTagType(level) {
  const map = { '无': 'info', '低': 'success', '中等': 'warning', '中高': 'warning', '高': 'danger', '极高': 'danger' }
  return map[level] || 'info'
}

function severityTagType(severity) {
  if (!severity) return 'info'
  if (severity.includes('严重') || severity.includes('爆发')) return 'danger'
  if (severity.includes('中度')) return 'warning'
  if (severity.includes('轻度') || severity.includes('一般')) return 'success'
  return 'info'
}

function chemTypeTag(type) {
  if (!type) return 'info'
  if (type.includes('保护')) return 'info'
  if (type.includes('治疗')) return 'warning'
  if (type.includes('铲除')) return 'danger'
  if (type.includes('内吸')) return 'success'
  return 'info'
}

function triggerUpload() {
  if (!previewUrl.value) {
    fileInput.value?.click()
  }
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return

  const validTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG、PNG、WEBP 格式的图片')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }

  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  prediction.value = null
  errorMsg.value = ''
  diagnosisResult.value = null
}

function handleDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    handleFileChange({ target: { files: [file] } })
  }
}

function formatFileSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(date) {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function generateReportId() {
  return Date.now().toString().slice(-8)
}

function resetUpload() {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  prediction.value = null
  errorMsg.value = ''
  diagnosisResult.value = null
  activeReportPanels.value = ['symptoms', 'treatment']
}

async function predict() {
  if (!selectedFile.value) {
    ElMessage.warning('请先上传叶片图像')
    return
  }

  predicting.value = true
  errorMsg.value = ''
  prediction.value = null
  diagnosisResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await modelApi.predict(formData)
    prediction.value = res
  } catch (e) {
    console.error('Prediction failed:', e)
    errorMsg.value = '识别失败，请检查网络连接或稍后重试'
    ElMessage.error('识别失败')
  } finally {
    predicting.value = false
  }
}

async function fetchDiagnosis() {
  if (!prediction.value) return

  diagnosing.value = true
  diagnosisResult.value = null

  try {
    const query = prediction.value.rag_key || prediction.value.disease_name
    const res = await modelApi.diagnose(query)
    diagnosisResult.value = res
  } catch (e) {
    console.error('Diagnosis fetch failed:', e)
    ElMessage.error('获取诊断报告失败')
    diagnosisResult.value = { summary: '无法获取诊断报告，请稍后重试。' }
  } finally {
    diagnosing.value = false
  }
}

function quickQuery(disease) {
  diagnosisResult.value = null
  diagnosing.value = true
  modelApi.diagnose(disease).then(res => {
    diagnosisResult.value = res
    diagnosing.value = false
  }).catch(() => {
    diagnosing.value = false
  })
}

function downloadReport() {
  if (!diagnosisResult.value) return
  downloadDialogVisible.value = true
}

async function downloadAs(format) {
  downloadDialogVisible.value = false
  
  if (!reportRef.value) {
    ElMessage.error('未找到报告内容')
    return
  }

  const originalPanels = [...activeReportPanels.value]
  const allPanels = ['symptoms', 'causes', 'chemicals', 'treatment', 'prevention', 'precautions', 'related']
  
  activeReportPanels.value = allPanels.filter(p => {
    const key = p === 'symptoms' ? diagnosisResult.value.symptoms :
                p === 'causes' ? diagnosisResult.value.causes :
                p === 'chemicals' ? diagnosisResult.value.recommended_chemicals :
                p === 'treatment' ? diagnosisResult.value.treatment_plan :
                p === 'prevention' ? diagnosisResult.value.prevention :
                p === 'precautions' ? diagnosisResult.value.precautions :
                p === 'related' ? diagnosisResult.value.related_diseases : null
    return key && key.length
  })

  if (reportFooterRef.value) {
    reportFooterRef.value.style.display = 'none'
  }

  await new Promise(resolve => setTimeout(resolve, 500))

  try {
    const canvas = await html2canvas(reportRef.value, {
      scale: 2,
      backgroundColor: '#ffffff',
      useCORS: true,
      allowTaint: true
    })

    if (format === 'png') {
      const link = document.createElement('a')
      link.download = `诊断报告_${prediction.value?.disease_name}_${Date.now()}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
      ElMessage.success('PNG图片已下载')
    } else if (format === 'pdf') {
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4'
      })

      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = canvas.width
      const imgHeight = canvas.height
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)
      const imgX = (pdfWidth - imgWidth * ratio) / 2
      const imgY = 10
      const imgDisplayWidth = imgWidth * ratio
      const imgDisplayHeight = imgHeight * ratio

      if (imgDisplayHeight <= pdfHeight - 20) {
        pdf.addImage(imgData, 'PNG', imgX, imgY, imgDisplayWidth, imgDisplayHeight)
      } else {
        let heightLeft = imgDisplayHeight
        let position = imgY

        pdf.addImage(imgData, 'PNG', imgX, position, imgDisplayWidth, Math.min(imgDisplayHeight, pdfHeight - 20))
        heightLeft -= pdfHeight - 20
        position = 10

        while (heightLeft > 0) {
          pdf.addPage()
          const h = Math.min(heightLeft, pdfHeight - 20)
          const sy = (imgHeight - heightLeft / ratio)
          pdf.addImage(imgData, 'PNG', imgX, position, imgDisplayWidth, h, undefined, undefined, undefined, sy)
          heightLeft -= pdfHeight - 20
        }
      }

      pdf.save(`诊断报告_${prediction.value?.disease_name}_${Date.now()}.pdf`)
      ElMessage.success('PDF报告已下载')
    }
  } catch (error) {
    console.error('Download failed:', error)
    ElMessage.error('下载失败，请重试')
  } finally {
    activeReportPanels.value = originalPanels
    if (reportFooterRef.value) {
      reportFooterRef.value.style.display = 'flex'
    }
  }
}
</script>

<style scoped>
.recognition-page {
  padding: 20px;
  width: 100%;
  min-height: calc(100vh - 48px);
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 50%, #ecfdf5 100%);
  position: relative;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  margin-bottom: 8px;
}

.header-icon {
  font-size: 28px;
}

.header-text h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.header-text p {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.header-text .el-tag {
  margin-top: 4px;
}

.upload-card, .result-card, .empty-card {
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: #409eff;
  background: #f0f5ff;
}

.hidden-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.placeholder-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f5ff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.placeholder-content {
  text-align: center;
}

.placeholder-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px;
}

.placeholder-hint {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-image-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.image-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.preview-image-wrapper:hover .image-overlay {
  opacity: 1;
}

.preview-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.action-area {
  padding-top: 16px;
  display: flex;
  justify-content: center;
}

.predict-btn {
  width: 220px;
  height: 44px;
  font-size: 15px;
  border-radius: 8px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.loading-icon {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 15px;
  color: #409eff;
  margin: 16px 0 8px;
}

.loading-hint {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.recognition-result {
  padding: 8px 0;
}

.result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.disease-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.confidence-bar {
  margin-bottom: 20px;
}

.bar-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.bar-container {
  width: 100%;
}

.confidence-progress {
  margin-bottom: 8px;
}

.confidence-hint {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 4px;
  display: inline-block;
}

.confidence-hint.success {
  background: #f0f9eb;
  color: #67c23a;
}

.confidence-hint.warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.confidence-hint.danger {
  background: #fef0f0;
  color: #f56c6c;
}

.symptoms-box {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 20px;
}

.box-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 10px;
}

.symptoms-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.symptom-tag {
  font-size: 12px;
}

.action-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
}

.action-divider span:first-child,
.action-divider span:last-child {
  flex: 1;
  height: 1px;
  background: #e4e7ed;
}

.divider-text {
  font-size: 12px;
  color: #909399;
}

.diagnosis-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: 8px;
}

.diagnosis-report {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  padding: 16px 20px;
  color: #fff;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.report-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
}

.report-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 20px;
  background: #fafafa;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  padding: 14px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.overview-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.overview-icon.success {
  background: #f0f9eb;
}

.overview-icon.warning {
  background: #fdf6ec;
}

.overview-icon.danger {
  background: #fef0f0;
}

.overview-icon.info {
  background: #ecf5ff;
}

.overview-content {
  flex: 1;
}

.overview-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.overview-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.summary-section {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.summary-content {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  text-indent: 2em;
}

.report-sections {
  padding: 0 20px;
}

.report-section {
  margin-bottom: 24px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
}

.report-section:last-child {
  margin-bottom: 0;
}

.precautions-section {
  border-color: #fbc4c4;
  background: #fef0f0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e4e7ed;
}

.precautions-section .section-header {
  background: #fde2e2;
  border-bottom-color: #fbc4c4;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.symptoms-icon {
  background: linear-gradient(135deg, #ecf5ff 0%, #dbeafe 100%);
}

.causes-icon {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}

.chemicals-icon {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
}

.treatment-icon {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
}

.prevention-icon {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.precautions-icon {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}

.related-icon {
  background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.section-content {
  padding: 16px;
}

.collapse-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.symptom-item, .treatment-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: #606266;
}

.item-number, .item-check {
  font-weight: 600;
  color: #409eff;
  flex-shrink: 0;
}

.item-check {
  color: #67c23a;
}

.cause-item, .prevention-item, .precaution-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: #606266;
}

.cause-item .el-icon, .precaution-item .el-icon {
  margin-top: 4px;
}

.chemicals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.chemical-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 14px;
}

.chem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chem-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.chem-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chem-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.row-icon {
  font-size: 14px;
}

.chem-row.safety {
  color: #f56c6c;
  font-weight: 500;
}

.related-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.related-tags .el-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.related-tags .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.report-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e4e7ed;
}

.empty-card {
  background: linear-gradient(135deg, #f0f9eb 0%, #ecf5ff 100%);
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

.error-alert {
  margin-top: 16px;
}

.download-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.download-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.download-option:hover {
  border-color: #409eff;
  background: #f0f5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.option-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.pdf-icon {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
}

.png-icon {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
}

.option-content {
  flex: 1;
}

.option-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.option-desc {
  font-size: 13px;
  color: #909399;
}
</style>
