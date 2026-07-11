<template>
  <div class="about-page">
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
        <div class="nav-item" @click="$router.push('/knowledge-graph')">
          <i class="fas fa-project-diagram"></i><span>知识图谱</span>
        </div>
        <div class="nav-item active" @click="$router.push('/about')">
          <i class="fas fa-info-circle"></i><span>关于系统</span>
        </div>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="main-content">
      <div class="about-card">
        <h1>水果病虫害智能诊断系统</h1>
        <p class="subtitle">基于深度学习的苹果与樱桃叶片病虫害检测与RAG诊断系统</p>

        <el-divider />

        <section>
          <h2>系统架构</h2>
          <div class="arch-grid">
            <div class="arch-item">
              <el-icon :size="32" color="#2563eb"><Cpu /></el-icon>
              <h3>深度学习模型</h3>
              <p>LSNet轻量级网络，结合知识蒸馏技术，对苹果、樱桃9类叶片病虫害进行高精度识别</p>
            </div>
            <div class="arch-item">
              <el-icon :size="32" color="#059669"><Reading /></el-icon>
              <h3>RAG知识库</h3>
              <p>基于检索增强生成技术，整合病害知识图谱，提供精准的诊断建议和防治方案</p>
            </div>
            <div class="arch-item">
              <el-icon :size="32" color="#8b5cf6"><Share /></el-icon>
              <h3>知识图谱</h3>
              <p>构建作物-病害-症状-防治多维度关联图谱，支持可视化查询和推理分析</p>
            </div>
            <div class="arch-item">
              <el-icon :size="32" color="#f59e0b"><ChatDotSquare /></el-icon>
              <h3>AI助手</h3>
              <p>智能问答系统，支持多轮对话、图片识别，为用户提供全方位的农业技术咨询</p>
            </div>
          </div>
        </section>

        <el-divider />

        <section>
          <h2>技术栈</h2>
          <el-table :data="techStack" stripe style="width: 100%">
            <el-table-column prop="layer" label="层次" width="120" />
            <el-table-column prop="tech" label="技术" />
            <el-table-column prop="desc" label="说明" />
          </el-table>
        </section>

        <el-divider />

        <section>
          <h2>模型性能</h2>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="基准准确率">90.91%</el-descriptions-item>
            <el-descriptions-item label="蒸馏模型">93.18%</el-descriptions-item>
            <el-descriptions-item label="教师模型">95.45%</el-descriptions-item>
            <el-descriptions-item label="Top-2准确率">98.86%</el-descriptions-item>
            <el-descriptions-item label="模型架构">LSNet</el-descriptions-item>
            <el-descriptions-item label="输入尺寸">256×256</el-descriptions-item>
          </el-descriptions>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
const techStack = [
  { layer: '前端', tech: 'Vue 3 + Element Plus', desc: '响应式单页应用，用户交互界面' },
  { layer: '后端', tech: 'Flask (Python)', desc: 'RESTful API，模型推理服务' },
  { layer: '深度学习', tech: 'PyTorch + LSNet', desc: '轻量级卷积神经网络，知识蒸馏' },
  { layer: '知识库', tech: 'RAG + JSON', desc: '检索增强生成，结构化知识管理' },
  { layer: '可视化', tech: 'SVG', desc: '知识图谱交互可视化' }
]
</script>

<style scoped>
.about-page { display: flex; min-height: 100vh; }

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
  flex: 1; margin-left: 220px; padding: 40px 32px;
  max-width: 1000px;
}

.about-card {
  background: #fff; border-radius: 16px; padding: 40px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.about-card h1 { font-size: 28px; color: #1e293b; text-align: center; }
.subtitle { text-align: center; color: #64748b; margin-top: 8px; }
section { margin: 24px 0; }
section h2 { font-size: 20px; color: #1e293b; margin-bottom: 16px; }

.arch-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
.arch-item {
  padding: 24px; border: 1px solid #e5e7eb; border-radius: 12px;
  text-align: center;
}
.arch-item h3 { font-size: 16px; color: #1e293b; margin: 12px 0 8px; }
.arch-item p { font-size: 14px; color: #64748b; line-height: 1.6; }
</style>
