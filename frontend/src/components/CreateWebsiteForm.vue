<template>
  <div class="create-website-form">
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent="handleSubmit"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h3>基本信息</h3>
        <el-form-item label="网站名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入网站名称，如：example"
            @blur="generateDomain"
          />
          <div class="form-tip">网站名称将用作目录名，建议使用英文</div>
        </el-form-item>

        <el-form-item label="主域名" prop="domain">
          <el-input
            v-model="form.domain"
            placeholder="请输入主域名，如：example.com"
          />
          <div class="form-tip">网站的主要访问域名</div>
        </el-form-item>

        <el-form-item label="其他域名" prop="domains">
          <el-input
            v-model="domainsText"
            type="textarea"
            :rows="3"
            placeholder="每行一个域名，如：&#10;www.example.com&#10;m.example.com"
            @input="updateDomains"
          />
          <div class="form-tip">可选，绑定多个域名到同一网站</div>
        </el-form-item>
      </div>

      <!-- 环境配置 -->
      <div class="form-section">
        <h3>环境配置</h3>
        <el-form-item label="PHP版本" prop="php_version">
          <el-select v-model="form.php_version" style="width: 100%;">
            <el-option label="PHP 8.2" value="8.2" />
            <el-option label="PHP 8.1" value="8.1" />
            <el-option label="PHP 8.0" value="8.0" />
            <el-option label="PHP 7.4" value="7.4" />
            <el-option label="PHP 7.3" value="7.3" />
            <el-option label="纯静态" value="static" />
          </el-select>
        </el-form-item>

        <el-form-item label="网站目录" prop="path">
          <el-input
            v-model="form.path"
            placeholder="网站文件存放路径"
            readonly
          />
          <div class="form-tip">系统自动生成，通常为 /www/wwwroot/网站名称</div>
        </el-form-item>

        <el-form-item label="默认文档">
          <el-input
            v-model="form.index_files"
            placeholder="index.html,index.htm,index.php"
          />
          <div class="form-tip">网站默认首页文件，多个用逗号分隔</div>
        </el-form-item>
      </div>

      <!-- 数据库配置 -->
      <div class="form-section">
        <h3>数据库配置</h3>
        <el-form-item>
          <el-checkbox v-model="createDatabase">同时创建数据库</el-checkbox>
        </el-form-item>

        <template v-if="createDatabase">
          <el-form-item label="数据库名" prop="database_name">
            <el-input
              v-model="form.database_name"
              placeholder="数据库名称"
            />
          </el-form-item>

          <el-form-item label="数据库用户" prop="database_user">
            <el-input
              v-model="form.database_user"
              placeholder="数据库用户名"
            />
          </el-form-item>

          <el-form-item label="数据库密码" prop="database_password">
            <el-input
              v-model="form.database_password"
              type="password"
              placeholder="数据库密码"
              show-password
            />
            <el-button
              type="text"
              size="small"
              @click="generatePassword"
              style="margin-left: 8px;"
            >
              生成密码
            </el-button>
          </el-form-item>
        </template>
      </div>

      <!-- SSL配置 -->
      <div class="form-section">
        <h3>SSL配置</h3>
        <el-form-item label="SSL证书" prop="ssl_type">
          <el-radio-group v-model="form.ssl_type">
            <el-radio label="none">不使用SSL</el-radio>
            <el-radio label="lets_encrypt">Let's Encrypt (免费)</el-radio>
            <el-radio label="self_signed">自签名证书</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.ssl_type === 'lets_encrypt'">
          <el-checkbox v-model="form.ssl_auto_renew">自动续期</el-checkbox>
          <div class="form-tip">建议开启，系统将自动续期SSL证书</div>
        </el-form-item>
      </div>

      <!-- 高级选项 -->
      <div class="form-section">
        <h3>高级选项</h3>
        <el-form-item>
          <el-checkbox v-model="form.gzip_enable">启用Gzip压缩</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="form.proxy_cache">启用代理缓存</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="form.backup_enable">启用自动备份</el-checkbox>
        </el-form-item>

        <el-form-item v-if="form.backup_enable" label="备份保留">
          <el-input-number
            v-model="form.backup_keep_days"
            :min="1"
            :max="30"
            style="width: 120px;"
          />
          <span style="margin-left: 8px;">天</span>
        </el-form-item>
      </div>
    </el-form>

    <!-- 操作按钮 -->
    <div class="form-actions">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ submitting ? '创建中...' : '创建网站' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['success', 'cancel'])

const formRef = ref()
const submitting = ref(false)
const createDatabase = ref(false)
const domainsText = ref('')

const form = reactive({
  name: '',
  domain: '',
  domains: [],
  php_version: '8.1',
  path: '',
  index_files: 'index.html,index.htm,index.php',
  ssl_type: 'none',
  ssl_auto_renew: true,
  gzip_enable: true,
  proxy_cache: false,
  backup_enable: false,
  backup_keep_days: 7,
  database_name: '',
  database_user: '',
  database_password: ''
})

const rules = {
  name: [
    { required: true, message: '请输入网站名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '网站名称只能包含字母、数字、下划线和横线', trigger: 'blur' }
  ],
  domain: [
    { required: true, message: '请输入主域名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/, message: '请输入有效的域名', trigger: 'blur' }
  ],
  path: [
    { required: true, message: '网站目录不能为空', trigger: 'blur' }
  ],
  database_name: [
    { required: createDatabase, message: '请输入数据库名称', trigger: 'blur' }
  ],
  database_user: [
    { required: createDatabase, message: '请输入数据库用户名', trigger: 'blur' }
  ],
  database_password: [
    { required: createDatabase, message: '请输入数据库密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ]
}

// 监听网站名称变化，自动生成路径
watch(() => form.name, (newName) => {
  if (newName) {
    form.path = `/www/wwwroot/${newName}`
    if (createDatabase.value && !form.database_name) {
      form.database_name = newName.replace(/[^a-zA-Z0-9_]/g, '_')
      form.database_user = form.database_name
    }
  }
})

// 根据网站名称生成域名
const generateDomain = () => {
  if (form.name && !form.domain) {
    form.domain = `${form.name}.com`
  }
}

// 更新其他域名
const updateDomains = () => {
  form.domains = domainsText.value
    .split('\n')
    .map(domain => domain.trim())
    .filter(domain => domain)
}

// 生成随机密码
const generatePassword = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
  let password = ''
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  form.database_password = password
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        ElMessage.success('网站创建成功')
        emit('success')
      } catch (error) {
        ElMessage.error('网站创建失败')
      } finally {
        submitting.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.create-website-form {
  .form-section {
    margin-bottom: 32px;
    
    h3 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      border-bottom: 1px solid #e4e7ed;
      padding-bottom: 8px;
    }
    
    .form-tip {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid #e4e7ed;
  }
}
</style>
