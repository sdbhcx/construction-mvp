<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { HomeFilled, Document, Search, DataAnalysis } from '@element-plus/icons-vue'

// 数据状态
const stats = ref({})
const records = ref([])
const isLoading = ref(false)

// 施工记录表单
const recordForm = ref({
  project_id: 'proj-001',
  date: new Date().toISOString().split('T')[0],
  activity_type: '混凝土浇筑',
  quantity: null,
  unit: '方',
  location: 'A区',
  description: '',
  workers_count: null,
  equipment: '',
  issues: ''
})

// 上传文件
const uploadFile = ref(null)

// 查询相关
const queryText = ref('')
const queryResult = ref(null)
const queryLoading = ref(false)

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await axios.get('/api/stats')
    if (response.data.success) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取施工记录
const fetchRecords = async () => {
  try {
    isLoading.value = true
    const response = await axios.get('/api/records')
    if (response.data.success) {
      records.value = response.data.data
    }
  } catch (error) {
    console.error('获取施工记录失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 提交施工记录
const submitRecord = async () => {
  try {
    const formData = new FormData()
    
    // 添加表单数据
    formData.append('record', JSON.stringify(recordForm.value))
    
    // 添加文件
    if (uploadFile.value) {
      formData.append('file', uploadFile.value)
    }
    
    const response = await axios.post('/api/records', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      // 清空表单
      recordForm.value = {
        project_id: 'proj-001',
        date: new Date().toISOString().split('T')[0],
        activity_type: '混凝土浇筑',
        quantity: null,
        unit: '方',
        location: 'A区',
        description: '',
        workers_count: null,
        equipment: '',
        issues: ''
      }
      uploadFile.value = null
      
      // 重新获取记录
      await fetchRecords()
      await fetchStats()
      
      ElMessage.success('施工记录创建成功！')
    }
  } catch (error) {
    console.error('提交施工记录失败:', error)
    ElMessage.error('施工记录创建失败，请重试！')
  }
}

// 执行自然语言查询
const executeQuery = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入查询内容！')
    return
  }
  
  try {
    queryLoading.value = true
    const response = await axios.post('/api/query', {
      question: queryText.value
    })
    
    if (response.data.success) {
      queryResult.value = response.data
    }
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败，请重试！')
  } finally {
    queryLoading.value = false
  }
}

// 组件挂载时获取数据
onMounted(async () => {
  await fetchStats()
  await fetchRecords()
})
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <h1>施工进度智能记录与查询系统</h1>
    </header>
    
    <!-- 主内容区 -->
    <main class="app-main">
      <!-- 左侧菜单 -->
      <aside class="app-sidebar">
        <el-menu default-active="1" class="el-menu-vertical-demo">
          <el-menu-item index="1">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon><Document /></el-icon>
            <span>施工记录</span>
          </el-menu-item>
          <el-menu-item index="3">
            <el-icon><Search /></el-icon>
            <span>智能查询</span>
          </el-menu-item>
          <el-menu-item index="4">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计分析</span>
          </el-menu-item>
        </el-menu>
      </aside>
      
      <!-- 右侧内容 -->
      <section class="app-content">
        <!-- 数据统计卡片 -->
        <div class="stats-section">
          <h2>数据统计</h2>
          <div class="stats-grid">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>总施工记录</span>
                </div>
              </template>
              <div class="card-content">
                <el-statistic :value="stats.total_records || 0" suffix="条" />
              </div>
            </el-card>
            
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>混凝土总方量</span>
                </div>
              </template>
              <div class="card-content">
                <el-statistic :value="stats.total_concrete || 0" suffix="方" />
              </div>
            </el-card>
            
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>近7天平均工人</span>
                </div>
              </template>
              <div class="card-content">
                <el-statistic :value="stats.avg_workers_7d || 0" suffix="人" :precision="1" />
              </div>
            </el-card>
            
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>问题记录数量</span>
                </div>
              </template>
              <div class="card-content">
                <el-statistic :value="stats.problem_count || 0" suffix="条" />
              </div>
            </el-card>
          </div>
        </div>
        
        <!-- 内容区域布局 -->
        <div class="content-layout">
          <!-- 左侧：施工记录列表 -->
          <div class="records-section">
            <h2>施工记录</h2>
            <el-table v-loading="isLoading" :data="records" style="width: 100%" stripe>
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="activity_type" label="施工活动" width="150" />
              <el-table-column prop="location" label="位置" width="100" />
              <el-table-column prop="quantity" label="数量" width="80">
                <template #default="scope">
                  {{ scope.row.quantity }} {{ scope.row.unit }}
                </template>
              </el-table-column>
              <el-table-column prop="workers_count" label="工人数量" width="100" />
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
              <el-table-column prop="issues" label="问题" show-overflow-tooltip />
              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="scope">
                  {{ new Date(scope.row.created_at).toLocaleString() }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <!-- 右侧：表单和查询 -->
          <div class="right-panel">
            <!-- 图片上传表单 -->
            <div class="upload-section">
              <h2>添加施工记录</h2>
              <el-form :model="recordForm" label-width="100px" size="small">
                <el-form-item label="项目ID">
                  <el-input v-model="recordForm.project_id" />
                </el-form-item>
                
                <el-form-item label="日期">
                  <el-date-picker v-model="recordForm.date" type="date" format="YYYY-MM-DD" />
                </el-form-item>
                
                <el-form-item label="施工活动">
                  <el-select v-model="recordForm.activity_type" placeholder="请选择">
                    <el-option label="混凝土浇筑" value="混凝土浇筑" />
                    <el-option label="钢筋绑扎" value="钢筋绑扎" />
                    <el-option label="模板安装" value="模板安装" />
                    <el-option label="土方开挖" value="土方开挖" />
                    <el-option label="防水施工" value="防水施工" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="数量">
                  <el-input-number v-model="recordForm.quantity" :min="0" :step="0.1" />
                </el-form-item>
                
                <el-form-item label="单位">
                  <el-input v-model="recordForm.unit" />
                </el-form-item>
                
                <el-form-item label="位置">
                  <el-input v-model="recordForm.location" />
                </el-form-item>
                
                <el-form-item label="工人数量">
                  <el-input-number v-model="recordForm.workers_count" :min="0" :step="1" />
                </el-form-item>
                
                <el-form-item label="设备">
                  <el-input v-model="recordForm.equipment" placeholder="例如：挖掘机、混凝土泵车" />
                </el-form-item>
                
                <el-form-item label="问题描述">
                  <el-input v-model="recordForm.issues" type="textarea" :rows="2" />
                </el-form-item>
                
                <el-form-item label="图片上传">
                  <el-upload
                    v-model="uploadFile"
                    class="upload-demo"
                    action=""
                    :auto-upload="false"
                    :on-change="(file) => uploadFile = file.raw"
                    :limit="1"
                    accept=".jpg,.jpeg,.png"
                  >
                    <el-button type="primary">点击上传</el-button>
                    <template #tip>
                      <div class="el-upload__tip">
                        只能上传 JPG/PNG 文件，且不超过 5MB
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="submitRecord" :loading="isLoading">
                    提交记录
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
            
            <!-- 智能查询 -->
            <div class="query-section">
              <h2>智能查询</h2>
              <el-input
                v-model="queryText"
                placeholder="例如：上周浇筑了多少混凝土？"
                clearable
                @keyup.enter="executeQuery"
              >
                <template #append>
                  <el-button type="primary" @click="executeQuery" :loading="queryLoading">
                    <el-icon><Search /></el-icon>
                    查询
                  </el-button>
                </template>
              </el-input>
              
              <!-- 查询结果 -->
              <div v-if="queryResult" class="query-result">
                <h3>查询结果</h3>
                <el-alert :title="queryResult.answer" type="info" show-icon />
                
                <div v-if="queryResult.data && queryResult.data.length > 0" class="result-data">
                  <h4>详细数据</h4>
                  <el-table :data="queryResult.data" size="small" style="width: 100%">
                    <el-table-column prop="date" label="日期" width="120" />
                    <el-table-column prop="activity_type" label="施工活动" width="150" />
                    <el-table-column prop="location" label="位置" width="100" />
                    <el-table-column prop="quantity" label="数量" width="100">
                      <template #default="scope">
                        {{ scope.row.quantity }} {{ scope.row.unit }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="workers_count" label="工人数量" width="100" />
                  </el-table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: Arial, sans-serif;
}

.app-header {
  background-color: #409EFF;
  color: white;
  padding: 0 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.app-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 200px;
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.app-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f0f2f5;
}

.stats-section,
.records-section,
.upload-section,
.query-section {
  margin-bottom: 20px;
  background-color: white;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stats-section h2,
.records-section h2,
.upload-section h2,
.query-section h2 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.card-content {
  text-align: center;
  padding: 20px 0;
}

.content-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.upload-section {
  margin-bottom: 20px;
}

.query-section {
  margin-top: 20px;
}

.query-result {
  margin-top: 16px;
  padding: 16px;
  background-color: #f0f9eb;
  border-radius: 4px;
}

.query-result h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.result-data {
  margin-top: 16px;
}

.result-data h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
}
</style>
