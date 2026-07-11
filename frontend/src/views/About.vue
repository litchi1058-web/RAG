<template>
  <div class="about-page">
    <header class="about-header">
      <div class="header-left">
        <span class="header-title">🌾 病虫害智能诊断系统</span>
      </div>
      <div class="header-right">
        <el-button text size="small" @click="$router.push('/')">
          <el-icon><ArrowLeft /></el-icon>返回首页
        </el-button>
      </div>
    </header>

    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">🌾 关于病虫害智能诊断系统</h1>
        <p class="hero-desc">基于深度学习和知识图谱的作物病害智能识别与防治平台</p>
      </div>
    </section>

    <div class="content-grid">
      <section class="info-card">
        <div class="card-icon">🎯</div>
        <h2>系统概述</h2>
        <p>本系统是一个面向农业领域的智能病害诊断平台，利用深度学习模型和知识图谱技术，为农户提供快速、准确的作物病害识别与防治建议服务。</p>
      </section>

      <section class="info-card">
        <div class="card-icon">⚡</div>
        <h2>核心优势</h2>
        <ul>
          <li><strong>AI驱动：</strong>基于Qwen本地大模型和深度学习模型</li>
          <li><strong>知识图谱：</strong>构建完整的病害知识网络</li>
          <li><strong>RAG技术：</strong>检索增强生成，精准问答</li>
          <li><strong>多作物支持：</strong>覆盖8种主要农作物</li>
        </ul>
      </section>
    </div>

    <section class="features-section">
      <h2 class="section-title">📋 功能模块</h2>
      <div class="features-grid">
        <div class="feature-card" @click="$router.push('/recognition/detect')">
          <div class="feature-icon">🔬</div>
          <h3>病害识别</h3>
          <p>拍照上传作物图片，AI实时诊断病害类型和严重程度</p>
          <span class="feature-link">立即体验 →</span>
        </div>
        <div class="feature-card" @click="$router.push('/rag/rag-query')">
          <div class="feature-icon">🤖</div>
          <h3>智能问答</h3>
          <p>基于RAG检索增强的智能问答系统，提供精准防治建议</p>
          <span class="feature-link">立即体验 →</span>
        </div>
        <div class="feature-card" @click="$router.push('/rag/knowledge')">
          <div class="feature-icon">📖</div>
          <h3>知识管理</h3>
          <p>管理病害知识库，维护病害信息和防治方案</p>
          <span class="feature-link">立即体验 →</span>
        </div>
        <div class="feature-card" @click="$router.push('/rag/knowledge-graph')">
          <div class="feature-icon">🕸️</div>
          <h3>知识图谱</h3>
          <p>可视化展示病害关系网络，探索病害之间的关联</p>
          <span class="feature-link">立即体验 →</span>
        </div>
        <div class="feature-card" @click="$router.push('/rag/diagnosis')">
          <div class="feature-icon">📋</div>
          <h3>诊断记录</h3>
          <p>查询历史诊断记录，追踪病害防治效果</p>
          <span class="feature-link">立即体验 →</span>
        </div>
      </div>
    </section>

    <section class="tech-stack">
      <h2 class="section-title">🛠️ 技术栈</h2>
      <div class="tech-grid">
        <div class="tech-item">Vue 3</div>
        <div class="tech-item">Element Plus</div>
        <div class="tech-item">FastAPI</div>
        <div class="tech-item">Qwen</div>
        <div class="tech-item">Neo4j</div>
        <div class="tech-item">SQLAlchemy</div>
      </div>
    </section>

    <section class="contact-section">
      <h2 class="section-title">📞 联系方式</h2>
      <div class="contact-info">
        <p>如有问题或建议，请联系系统管理员</p>
      </div>
    </section>

    <footer class="about-footer">
      <div class="footer-content">
        <span>© 2026 病虫害智能诊断系统</span>
        <span>|</span>
        <span><a href="/" class="footer-link">首页</a></span>
        <span><a href="/about" class="footer-link">关于系统</a></span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'
</script>

<style scoped>
.about-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #fdf4ff 0%, #f0fdf4 50%, #f8fafc 100%);
  padding-bottom: 60px;
}

.about-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  margin: 16px 20px;
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a237e;
}

.hero-section {
  margin: 0 20px;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
}

.hero-title {
  font-size: 28px;
  color: #fff;
  margin: 0 0 12px;
  font-weight: 700;
}

.hero-desc {
  font-size: 16px;
  color: rgba(255,255,255,0.8);
  margin: 0;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin: 16px 20px;
}

.info-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border: 1px solid #e8eaed;
}

.card-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.info-card h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px;
}

.info-card p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

.info-card ul {
  margin: 0;
  padding-left: 20px;
}

.info-card li {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.info-card li:last-child {
  margin-bottom: 0;
}

.features-section, .tech-stack, .contact-section {
  margin: 16px 20px;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border: 1px solid #e8eaed;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.feature-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all .3s;
  border: 1px solid #e5e7eb;
}

.feature-card:hover {
  background: #f0fdf4;
  border-color: #22c55e;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(34,197,94,0.1);
}

.feature-icon {
  font-size: 28px;
  margin-bottom: 12px;
}

.feature-card h3 {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.feature-card p {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 12px;
}

.feature-link {
  font-size: 13px;
  color: #22c55e;
  font-weight: 600;
}

.tech-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tech-item {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.contact-info p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.about-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  border-top: 1px solid #e8eaed;
  padding: 12px 24px;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
}

.footer-link {
  color: #22c55e;
  text-decoration: none;
}

.footer-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .about-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  .hero-title {
    font-size: 22px;
  }
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>