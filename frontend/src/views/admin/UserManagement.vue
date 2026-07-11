<template>
  <div class="user-mgmt">
    <div class="mgmt-header">
      <h2>用户与权限</h2>
      <el-button type="primary" size="default" @click="openCreate">
        <el-icon><Plus /></el-icon> 新增用户
      </el-button>
    </div>

    <div class="user-table-card">
      <el-table :data="users" border stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column label="角色" width="140">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)" size="small">
            {{ roleLabel(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除该用户？" confirm-button-text="删除" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row.username === 'admin'">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑用户' : '新增用户'" width="420px" :close-on-click-modal="false">
      <el-form :model="form" label-width="80px" ref="formRef">
        <el-form-item label="用户名" prop="username" :rules="[{required:true,message:'请输入用户名'}]">
          <el-input v-model="form.username" placeholder="2-64 个字符" />
        </el-form-item>
        <el-form-item :label="isEditing ? '新密码' : '密码'" prop="password"
          :rules="isEditing ? [] : [{required:true,message:'请输入密码'}]">
          <el-input v-model="form.password" type="password"
            :placeholder="isEditing ? '留空则不修改' : '4-128 个字符'" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option label="数据管理员" value="data_manager" />
            <el-option label="普通农户" value="farmer" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active" v-if="isEditing">
          <el-switch v-model="form.is_active" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/api/request'

const users = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const form = ref({ username: '', password: '', role: 'farmer', is_active: 1 })

const roleLabel = (role) => ({ admin: '管理员', data_manager: '数据管理员', farmer: '普通农户' }[role] || role)
const roleTagType = (role) => ({ admin: 'danger', data_manager: 'warning', farmer: 'info' }[role] || 'info')
const formatDate = (dt) => dt ? dt.slice(0, 16).replace('T', ' ') : ''

async function loadUsers() {
  users.value = await request.get('/users')
}
onMounted(loadUsers)

function openCreate() {
  isEditing.value = false; editingId.value = null
  form.value = { username: '', password: '', role: 'farmer', is_active: 1 }
  dialogVisible.value = true
}

function openEdit(row) {
  isEditing.value = true; editingId.value = row.id
  form.value = { username: row.username, password: '', role: row.role, is_active: row.is_active ? 1 : 0 }
  dialogVisible.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEditing.value) {
      await request.put(`/users/${editingId.value}`, form.value)
      ElMessage.success('用户已更新')
    } else {
      await request.post('/users', form.value)
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch { /* handled */ }
  finally { saving.value = false }
}

async function handleDelete(row) {
  await request.delete(`/users/${row.id}`)
  ElMessage.success('用户已删除')
  await loadUsers()
}
</script>

<style scoped>
.user-mgmt { 
  width: 100%; 
  margin: 0; 
  padding: 24px; 
  min-height: calc(100vh - 56px); 
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 35%, #f8fafc 70%, #faf5ff 100%); 
  position: relative; 
}
.user-mgmt::before { 
  content: ''; 
  position: absolute; 
  inset: 0; 
  background: radial-gradient(circle at 25% 15%, rgba(59,130,246,0.08) 0%, transparent 50%), 
              radial-gradient(circle at 75% 85%, rgba(46,125,50,0.08) 0%, transparent 50%); 
  pointer-events: none; 
}
.user-mgmt::after {
  content: '';
  position: absolute;
  bottom: -200px;
  right: -200px;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: bg-float 12s ease-in-out infinite;
}
@keyframes bg-float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, -40px); }
}

.mgmt-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 28px; 
}
.mgmt-header h2 { 
  margin: 0; 
  font-size: 28px; 
  font-weight: 800; 
  color: #1a237e; 
  letter-spacing: -0.3px; 
}

.user-table-card {
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 8px 32px rgba(0,0,0,0.03);
  overflow: hidden;
  transition: all .4s;
}
.user-table-card:hover {
  box-shadow: 0 12px 40px rgba(0,0,0,0.06);
}
</style>