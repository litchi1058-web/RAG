<template>
  <div class="chat-page">
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
        <div class="nav-item active" @click="$router.push('/chat')">
          <i class="fas fa-robot"></i><span>AI助手</span>
        </div>
        <div class="nav-item" @click="$router.push('/knowledge-graph')">
          <i class="fas fa-project-diagram"></i><span>知识图谱</span>
        </div>
        <div class="nav-item" @click="$router.push('/about')">
          <i class="fas fa-info-circle"></i><span>关于系统</span>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="header-left">
          <i class="fas fa-comments"></i>
          <h1>AI 智能问答</h1>
        </div>
        <el-button size="small" @click="clearChat" :icon="'Delete'">清空对话</el-button>
      </div>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="welcome-icon">🌱</div>
          <h2>欢迎使用AI智能问答系统</h2>
          <p>上传图片进行病害识别，或直接咨询农业问题</p>
          <div class="welcome-features">
            <div class="feature-item"><i class="fas fa-image"></i><span>图片识别</span></div>
            <div class="feature-item"><i class="fas fa-question-circle"></i><span>智能问答</span></div>
            <div class="feature-item"><i class="fas fa-book-open"></i><span>专业知识</span></div>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <div class="avatar">{{ msg.role === 'user' ? '👨‍🌾' : '🧠' }}</div>
          <div class="message-body">
            <div class="message-header">
              <span class="name">{{ msg.role === 'user' ? '我' : 'AI助手' }}</span>
              <span class="time">{{ msg.time }}</span>
            </div>
            <div class="message-content">
              <img v-if="msg.image" :src="msg.image" class="msg-image" />
              <div class="msg-text" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="message assistant">
          <div class="avatar">🧠</div>
          <div class="message-body">
            <div class="message-header"><span class="name">AI助手</span></div>
            <div class="message-content">
              <div class="thinking"><span></span><span></span><span></span> 思考中...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷问题 -->
      <div v-if="quickQuestions.length > 0 && messages.length <= 1" class="quick-questions">
        <span class="qlabel">💡 快捷问题：</span>
        <el-tag
          v-for="q in quickQuestions"
          :key="q"
          @click="inputMessage = q"
          style="cursor: pointer"
        >
          {{ q }}
        </el-tag>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-toolbar">
          <el-upload
            :show-file-list="false"
            :auto-upload="false"
            accept="image/*"
            @change="handleImageSelect"
          >
            <el-button :icon="'PictureFilled'" size="small">图片</el-button>
          </el-upload>
          <div v-if="selectedImage" class="image-preview">
            <img :src="selectedImage" />
            <span class="remove" @click="removeImage">×</span>
          </div>
        </div>
        <div class="input-row">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="请输入您的问题，或上传图片进行识别..."
            @keydown.enter.prevent="handleEnter"
            :disabled="loading"
          />
          <el-button
            type="primary"
            :icon="'Promotion'"
            :disabled="(!inputMessage.trim() && !selectedImage) || loading"
            @click="sendMessage"
            class="send-btn"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ragQuery, predictImage } from '@/api'

const chatMessagesRef = ref(null)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const selectedImage = ref(null)
const selectedImageFile = ref(null)
const quickQuestions = ref([
  '苹果黑星病用什么药？',
  '安全间隔期是什么意思？',
  '怎么判断病害严重程度？'
])

function handleImageSelect(uploadFile) {
  const file = uploadFile.raw
  if (file && file.type.startsWith('image/')) {
    selectedImageFile.value = file
    selectedImage.value = URL.createObjectURL(file)
  }
}

function removeImage() {
  if (selectedImage.value) URL.revokeObjectURL(selectedImage.value)
  selectedImage.value = null
  selectedImageFile.value = null
}

function handleEnter(e) {
  if (!e.shiftKey) sendMessage()
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text && !selectedImageFile.value) return
  inputMessage.value = ''

  messages.value.push({
    role: 'user',
    content: text || '[图片识别]',
    time: formatTime(new Date()),
    image: selectedImage.value
  })

  loading.value = true
  scrollToBottom()

  try {
    if (selectedImageFile.value) {
      const fd = new FormData()
      fd.append('image', selectedImageFile.value)
      if (text) fd.append('message', text)
      const predRes = await predictImage(fd)
      if (predRes.success) {
        const pred = predRes.data || predRes
        const name = pred.predicted_class || pred.prediction?.predicted_class || '未知'
        messages.value.push({ role: 'assistant', content: '识别结果：' + name, time: formatTime(new Date()) })
      } else {
        messages.value.push({ role: 'assistant', content: '识别失败：' + (predRes.message || '未知错误'), time: formatTime(new Date()) })
      }
    } else {
      const res = await ragQuery(text)
      if (res && res.has_knowledge) {
        let reply = res.diagnostic_report || res.summary || ''
        if (res.causes?.length) reply += '\n\n【病因】\n' + res.causes.join('\n')
        if (res.symptoms?.length) reply += '\n\n【症状】\n' + res.symptoms.join('\n')
        if (res.recommended_chemicals?.length) reply += '\n\n【推荐药剂】' + res.recommended_chemicals.map(c => typeof c === 'string' ? c : c.name).join('、')
        messages.value.push({ role: 'assistant', content: reply, time: formatTime(new Date()) })
      } else {
        messages.value.push({ role: 'assistant', content: '未找到相关信息，请尝试其他问题', time: formatTime(new Date()) })
      }
    }
  } catch {
    messages.value.push({ role: 'assistant', content: '网络错误，请稍后重试', time: formatTime(new Date()) })
  } finally {
    loading.value = false
    removeImage()
    scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
  quickQuestions.value = [
    '苹果黑星病用什么药？',
    '安全间隔期是什么意思？',
    '怎么判断病害严重程度？'
  ]
}

function formatMessage(content) {
  if (!content) return ''
  let r = content.trim()
  r = r.replace(/^---\s*$/gm, '')
  r = r.replace(/\n{3,}/g, '\n\n')
  r = r.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  r = r.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  r = r.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>')
  r = r.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
  r = r.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
  r = r.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')
  r = r.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  r = r.replace(/\*(.+?)\*/g, '<em>$1</em>')
  r = r.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
  r = r.replace(/【(.+?)】/g, '<div class="card-title">$1</div>')
  r = r.replace(/^(?:-|\*|\+|\d+\.)\s+(.+)$/gm, '<li>$1</li>')
  r = r.replace(/(<li>[\s\S]*?<\/li>\s*)+/g, m => '<ul>' + m + '</ul>')
  r = r.replace(/\n/g, '<br>')
  return r
}

function formatTime(d) {
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatMessagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
</script>

<style scoped>
.chat-page {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  min-height: 100vh;
  background: #fff;
  border-right: 1px solid #eef2f8;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 10;
}
.logo {
  padding: 28px 20px; text-align: center;
  border-bottom: 1px solid #f0f3f9;
}
.logo h2 { font-size: 16px; color: #2563eb; margin-top: 8px; }
.logo p { font-size: 12px; color: #999; margin-top: 2px; }
.nav-list { padding: 12px 8px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; cursor: pointer;
  border-left: 3px solid transparent;
  border-radius: 0 8px 8px 0; margin-bottom: 4px; color: #555;
}
.nav-item:hover { background: #f8faff; color: #2563eb; }
.nav-item.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; font-weight: 500; }
.nav-item i { font-size: 18px; width: 20px; }

.chat-main {
  flex: 1; margin-left: 220px;
  display: flex; flex-direction: column;
  height: 100vh;
}

.chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; background: #fff;
  border-bottom: 1px solid #eef2f8;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left i { font-size: 20px; color: #2563eb; }
.header-left h1 { font-size: 18px; color: #1e293b; }

.chat-messages {
  flex: 1; overflow-y: auto; padding: 24px;
  background: #f8fafc;
}

.welcome-screen {
  text-align: center; padding: 80px 20px;
}
.welcome-icon { font-size: 64px; margin-bottom: 16px; }
.welcome-screen h2 { font-size: 22px; color: #1e293b; margin-bottom: 8px; }
.welcome-screen p { color: #64748b; margin-bottom: 24px; }
.welcome-features {
  display: flex; gap: 24px; justify-content: center;
}
.feature-item {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 20px 32px; background: #fff; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.feature-item i { font-size: 28px; color: #2563eb; }
.feature-item span { font-size: 14px; color: #374151; }

.message {
  display: flex; gap: 12px; margin-bottom: 20px;
}
.avatar {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.message-body { max-width: 75%; }
.message-header { display: flex; gap: 8px; margin-bottom: 4px; }
.name { font-size: 13px; font-weight: 500; color: #374151; }
.time { font-size: 12px; color: #9ca3af; }
.message-content {
  padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.7;
}
.message.user .message-content {
  background: #2563eb; color: #fff;
  border-bottom-right-radius: 4px;
}
.message.assistant .message-content {
  background: #fff; color: #1e293b;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.msg-image { max-width: 200px; border-radius: 8px; margin-bottom: 8px; display: block; }
.thinking { color: #9ca3af; }
.thinking span {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: #2563eb; margin: 0 2px;
  animation: bounce 1.4s infinite;
}
.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%,80%,100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.quick-questions {
  padding: 12px 24px; background: #fff;
  border-top: 1px solid #eef2f8;
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
}
.qlabel { font-size: 13px; color: #64748b; }

.chat-input {
  padding: 16px 24px; background: #fff;
  border-top: 1px solid #eef2f8;
}
.input-toolbar {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.image-preview {
  position: relative; display: inline-block;
}
.image-preview img { height: 48px; border-radius: 6px; }
.remove {
  position: absolute; top: -6px; right: -6px;
  width: 18px; height: 18px; border-radius: 50%;
  background: #ef4444; color: #fff; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.input-row { display: flex; gap: 12px; align-items: flex-start; }
.input-row .el-input { flex: 1; }
.send-btn { height: 52px; padding: 0 24px; }
</style>
