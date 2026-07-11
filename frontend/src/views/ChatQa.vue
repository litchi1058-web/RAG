<template>
  <div class="chat-container">
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-title">🤖 智能问答</div>
        <el-button class="new-chat-btn" @click="newChat" :icon="Plus" circle />
      </div>
      
      <div class="chat-list">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          :class="['chat-item', { active: currentChatId === chat.id }]"
          @click="selectChat(chat.id)"
        >
          <div class="chat-avatar">
            <User v-if="chat.is_user" />
            <ChatLineSquare v-else />
          </div>
          <div class="chat-info">
            <div class="chat-title">{{ chat.title }}</div>
            <div class="chat-preview">{{ chat.preview }}</div>
          </div>
          <div class="chat-time">{{ chat.time }}</div>
          <el-button 
            class="delete-chat-btn" 
            @click.stop="deleteChat(chat.id)"
            :icon="Delete" 
            circle 
            size="small"
          />
        </div>
      </div>

      <div class="quick-actions">
        <div class="action-title">快捷问题</div>
        <div 
          v-for="(question, index) in quickQuestions" 
          :key="index"
          class="quick-question"
          @click="sendQuickQuestion(question)"
        >
          <el-icon size="14"><HelpFilled /></el-icon>
          <span>{{ question }}</span>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div v-if="!currentChat" class="welcome-screen">
        <div class="welcome-icon">🌾</div>
        <h2>智能农业问答助手</h2>
        <p>基于RAG检索增强技术，为您提供专业的作物病害诊断和防治建议</p>
        <div class="welcome-actions">
          <el-button type="primary" @click="newChat">
            <ChatRound />
            开始新对话
          </el-button>
        </div>
      </div>

      <div v-else class="chat-view">
        <div class="chat-header">
          <div class="header-info">
            <ChatLineSquare :size="20" color="#409eff" />
            <span>{{ currentChatTitle }}</span>
          </div>
          <div class="header-actions">
            <el-button @click="clearChat" text size="small">
              <RefreshLeft /> 清空对话
            </el-button>
          </div>
        </div>

        <div class="message-list" ref="messageList">
          <div 
            v-for="(message, index) in currentMessages" 
            :key="index"
            :class="['message-item', { user: message.is_user }]"
          >
            <div class="message-avatar">
              <User v-if="message.is_user" />
              <div class="bot-avatar" v-else>🤖</div>
            </div>
            <div class="message-bubble">
              <div v-if="message.image" class="message-image">
                <img :src="message.image" />
              </div>
              <div v-if="message.recognition_result" class="recognition-card">
                <div class="recog-header">
                  <el-icon color="#67c23a"><Picture /></el-icon>
                  <span>图像识别结果</span>
                </div>
                <div class="recog-content">
                  <el-tag :type="message.recognition_result.confidence > 0.7 ? 'success' : 'warning'">
                    {{ message.recognition_result.disease_name }}
                  </el-tag>
                  <div class="recog-confidence">
                    置信度: {{ Math.round(message.recognition_result.confidence * 100) }}%
                  </div>
                </div>
              </div>
              <div v-if="message.entities && Object.keys(message.entities).length" class="entities-row">
                <span class="entity-label">识别实体:</span>
                <el-tag v-if="message.entities.crops?.length" type="success" size="small">
                  作物: {{ message.entities.crops.join(', ') }}
                </el-tag>
                <el-tag v-if="message.entities.diseases?.length" type="danger" size="small">
                  病害: {{ message.entities.diseases.join(', ') }}
                </el-tag>
                <el-tag v-if="message.entities.severity?.length" type="warning" size="small">
                  程度: {{ message.entities.severity.join(', ') }}
                </el-tag>
              </div>
              <div class="message-content" v-html="formatMessage(message.content)"></div>
              <div v-if="message.recommended_chemicals?.length" class="chemicals-row">
                <div class="chem-label">推荐药剂:</div>
                <div class="chem-items">
                  <el-card 
                    v-for="(chem, i) in message.recommended_chemicals" 
                    :key="i" 
                    class="chem-card"
                  >
                    <div class="chem-name">{{ chem.name }}</div>
                    <div class="chem-detail">
                      <span class="chem-type">{{ chem.type }}</span>
                      <span class="chem-dilution">稀释: {{ chem.dilution }}</span>
                    </div>
                  </el-card>
                </div>
              </div>
              <div v-if="message.treatment_plan?.length" class="treatment-row">
                <div class="treat-label">防治方案:</div>
                <ul class="treat-list">
                  <li v-for="(item, i) in message.treatment_plan" :key="i">
                    <el-icon color="#67c23a"><Check /></el-icon>
                    {{ item }}
                  </li>
                </ul>
              </div>
              <div v-if="message.prevention?.length" class="prevention-row">
                <div class="prevent-label">预防措施:</div>
                <ul class="prevent-list">
                  <li v-for="(item, i) in message.prevention" :key="i">
                    <el-icon color="#409eff"><Lock /></el-icon>
                    {{ item }}
                  </li>
                </ul>
              </div>
              <div v-if="message.suggestion" class="suggestion-row">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ message.suggestion }}</span>
              </div>
            </div>
          </div>

          <div v-if="loading" class="loading-item">
            <div class="loading-avatar">🤖</div>
            <div class="loading-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="input-tools">
            <el-button 
              class="tool-btn" 
              @click="triggerFileInput" 
              :icon="Upload" 
              circle 
              size="small"
              :disabled="loading"
            />
            <el-button 
              class="tool-btn" 
              @click="clearImage" 
              :icon="CircleClose" 
              circle 
              size="small"
              v-if="uploadedImage"
            />
          </div>
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="1"
              placeholder="输入您的问题，或上传图片进行诊断..."
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
              :disabled="loading"
            />
            <el-button 
              class="send-btn" 
              @click="sendMessage" 
              :icon="Promotion" 
              :loading="loading"
              :disabled="!canSend"
            />
          </div>
          <div v-if="uploadedImage" class="image-preview-bar">
            <img :src="uploadedImage" class="preview-thumb" />
            <span class="preview-text">已选择图片</span>
          </div>
        </div>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      class="hidden-file-input"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import {
  Plus, User, Delete, HelpFilled, ChatRound,
  RefreshLeft, Upload, CircleClose, Promotion, Check, Lock, InfoFilled, Picture, ChatLineSquare
} from '@element-plus/icons-vue'
import { ragApi } from '@/api/rag'

const chatHistory = ref([])
const currentChatId = ref(null)
const currentMessages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const uploadedImage = ref('')
const fileInput = ref(null)
const messageList = ref(null)

const quickQuestions = [
  '苹果黑星病的症状是什么',
  '樱桃白粉病用什么药',
  '如何预防苹果病害',
  '苹果黑斑病怎么治疗',
  '樱桃流胶病的原因',
  '如何识别苹果健康植株'
]

const currentChat = computed(() => {
  return chatHistory.value.find(c => c.id === currentChatId.value)
})

const currentChatTitle = computed(() => {
  return currentChat.value?.title || '新对话'
})

const canSend = computed(() => {
  return (inputMessage.value.trim() || uploadedImage.value) && !loading.value
})

onMounted(() => {
  loadChatHistory()
})

function loadChatHistory() {
  const stored = localStorage.getItem('chatHistory')
  if (stored) {
    try {
      chatHistory.value = JSON.parse(stored)
      if (chatHistory.value.length > 0) {
        currentChatId.value = chatHistory.value[0].id
        loadChat(currentChatId.value)
      }
    } catch {
      chatHistory.value = []
    }
  }
}

function saveChatHistory() {
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory.value))
}

function loadChat(chatId) {
  const stored = localStorage.getItem(`chat_${chatId}`)
  if (stored) {
    try {
      currentMessages.value = JSON.parse(stored)
    } catch {
      currentMessages.value = []
    }
  } else {
    currentMessages.value = []
  }
}

function saveCurrentChat() {
  if (currentChatId.value) {
    localStorage.setItem(`chat_${currentChatId.value}`, JSON.stringify(currentMessages.value))
  }
}

function newChat() {
  const newId = Date.now().toString()
  currentChatId.value = newId
  currentMessages.value = []
  inputMessage.value = ''
  uploadedImage.value = ''
  
  chatHistory.value.unshift({
    id: newId,
    title: '新对话',
    preview: '',
    time: formatTime(new Date()),
    is_user: false
  })
  saveChatHistory()
}

function selectChat(chatId) {
  currentChatId.value = chatId
  loadChat(chatId)
  inputMessage.value = ''
  uploadedImage.value = ''
}

function deleteChat(chatId) {
  chatHistory.value = chatHistory.value.filter(c => c.id !== chatId)
  localStorage.removeItem(`chat_${chatId}`)
  saveChatHistory()
  
  if (currentChatId.value === chatId) {
    if (chatHistory.value.length > 0) {
      currentChatId.value = chatHistory.value[0].id
      loadChat(currentChatId.value)
    } else {
      currentChatId.value = null
      currentMessages.value = []
    }
  }
}

function clearChat() {
  currentMessages.value = []
  saveCurrentChat()
  
  const chat = chatHistory.value.find(c => c.id === currentChatId.value)
  if (chat) {
    chat.title = '新对话'
    chat.preview = ''
    saveChatHistory()
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (event) => {
      uploadedImage.value = event.target.result
    }
    reader.readAsDataURL(file)
  }
}

function clearImage() {
  uploadedImage.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function autoResize() {
  nextTick(() => {
    const textarea = document.querySelector('.el-textarea__inner')
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
    }
  })
}

async function sendMessage() {
  if (!canSend.value) return
  
  const messageText = inputMessage.value.trim()
  if (!messageText && !uploadedImage.value) return
  
  const userMessage = {
    id: Date.now(),
    content: messageText,
    is_user: true,
    image: uploadedImage.value || null,
    timestamp: new Date().toISOString()
  }
  
  currentMessages.value.push(userMessage)
  saveCurrentChat()
  scrollToBottom()
  
  loading.value = true
  inputMessage.value = ''
  autoResize()
  
  try {
    let responseData = null
    
    if (uploadedImage.value) {
      const imageBase64 = uploadedImage.value.split(',')[1]
      responseData = await ragApi.predictImage({
        image: imageBase64,
        query: messageText
      })
    } else {
      responseData = await ragApi.query({ query: messageText, top_k: 5 })
    }
    
    const botMessage = {
      id: Date.now() + 1,
      content: responseData.chat_response?.response || responseData.summary || '暂无回答',
      is_user: false,
      timestamp: new Date().toISOString(),
      entities: responseData.entities,
      recommended_chemicals: responseData.recommended_chemicals,
      treatment_plan: responseData.treatment_plan,
      prevention: responseData.prevention,
      suggestion: responseData.suggestion,
      recognition_result: responseData.recognition_result
    }
    
    currentMessages.value.push(botMessage)
    saveCurrentChat()
    
    updateChatTitle(messageText, responseData)
    
  } catch (error) {
    const errorMessage = {
      id: Date.now() + 1,
      content: `查询失败: ${error.message || '未知错误'}`,
      is_user: false,
      timestamp: new Date().toISOString()
    }
    currentMessages.value.push(errorMessage)
    saveCurrentChat()
  } finally {
    loading.value = false
    uploadedImage.value = ''
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    scrollToBottom()
  }
}

function sendQuickQuestion(question) {
  inputMessage.value = question
  sendMessage()
}

function updateChatTitle(query, response) {
  const chat = chatHistory.value.find(c => c.id === currentChatId.value)
  if (chat) {
    const diseaseName = response.disease_name || query.substring(0, 20)
    chat.title = diseaseName
    chat.preview = response.summary || query.substring(0, 30) + '...'
    chat.time = formatTime(new Date())
    saveChatHistory()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

function formatTime(date) {
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatMessage(text) {
  if (!text) return ''
  let html = text.replace(/\n/g, '<br/>')
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/### (.*?)\n/g, '<h4>$1</h4>')
  html = html.replace(/## (.*?)\n/g, '<h3>$1</h3>')
  html = html.replace(/### (.*?)(?=\n|$)/g, '<h4>$1</h4>')
  html = html.replace(/## (.*?)(?=\n|$)/g, '<h3>$1</h3>')
  return html
}

watch(currentMessages, () => {
  saveCurrentChat()
}, { deep: true })
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 64px);
  width: 100%;
  background: #f5f7fa;
}

.sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e8ecf0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f2f5;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.new-chat-btn {
  width: 32px;
  height: 32px;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.chat-item:hover {
  background: #f5f7fa;
}

.chat-item.active {
  background: #e3f2fd;
}

.chat-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  color: #606266;
}

.bot-avatar {
  font-size: 18px;
}

.chat-info {
  flex: 1;
  overflow: hidden;
}

.chat-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-preview {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.chat-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-left: 8px;
}

.delete-chat-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-item:hover .delete-chat-btn {
  opacity: 1;
}

.quick-actions {
  padding: 16px;
  border-top: 1px solid #f0f2f5;
}

.action-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

.quick-question {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.quick-question:hover {
  background: #f5f7fa;
  color: #409eff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.welcome-screen h2 {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 12px;
}

.welcome-screen p {
  font-size: 15px;
  color: #606266;
  text-align: center;
  max-width: 400px;
  line-height: 1.6;
}

.welcome-actions {
  margin-top: 32px;
}

.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #409eff;
  color: #fff;
}

.message-item:not(.user) .message-avatar {
  background: #e8f5e9;
  font-size: 18px;
}

.message-bubble {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
}

.message-item.user .message-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-item:not(.user) .message-bubble {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.message-image {
  margin-bottom: 10px;
}

.message-image img {
  max-width: 100%;
  border-radius: 8px;
}

.recognition-card {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.recog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #67c23a;
  margin-bottom: 8px;
}

.recog-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.recog-confidence {
  font-size: 13px;
  color: #606266;
}

.entities-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.entity-label {
  font-size: 12px;
  color: #909399;
}

.message-content {
  white-space: pre-wrap;
}

.message-content h3 {
  font-size: 15px;
  margin: 12px 0 8px;
  color: #303133;
}

.message-content h4 {
  font-size: 14px;
  margin: 10px 0 6px;
  color: #606266;
}

.message-content strong {
  color: #409eff;
}

.message-item.user .message-content strong {
  color: #fff;
}

.chemicals-row {
  margin-top: 12px;
}

.chem-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.chem-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chem-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  min-width: 140px;
}

.chem-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.chem-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chem-type {
  font-size: 12px;
  color: #606266;
}

.chem-dilution {
  font-size: 12px;
  color: #909399;
}

.treatment-row, .prevention-row {
  margin-top: 12px;
}

.treat-label, .prevent-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.treat-list, .prevent-list {
  padding-left: 0;
  margin: 0;
}

.treat-list li, .prevent-list li {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 4px;
}

.suggestion-row {
  margin-top: 12px;
  padding: 10px 12px;
  background: linear-gradient(145deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #166534;
}

.loading-item {
  display: flex;
}

.loading-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e8f5e9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin-right: 12px;
}

.loading-bubble {
  background: #fff;
  padding: 16px 20px;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.input-area {
  background: #fff;
  padding: 16px 24px;
  border-top: 1px solid #f0f2f5;
}

.input-tools {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.tool-btn {
  width: 32px;
  height: 32px;
  color: #606266;
}

.tool-btn:hover {
  color: #409eff;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-wrapper :deep(.el-textarea) {
  flex: 1;
}

.input-wrapper :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  border-color: #dcdfe6;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex-shrink: 0;
}

.image-preview-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.preview-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 6px;
}

.preview-text {
  font-size: 13px;
  color: #606266;
}

.hidden-file-input {
  display: none;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}
</style>
