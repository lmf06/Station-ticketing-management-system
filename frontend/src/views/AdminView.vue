<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Plus, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, formatDateTime } from '../api'

const activeTab = ref('stations')
const stations = ref([])
const routes = ref([])
const vehicles = ref([])
const trips = ref([])
const fareRules = ref([])
const users = ref([])
const stats = ref({})
const loading = ref(false)
const userEditDialogOpen = ref(false)
const editingUser = ref(null)

const stationForm = reactive({ name: '', city: '', address: '' })
const routeForm = reactive({ code: '', name: '', originStationId: '', destinationStationId: '', distanceKm: '' })
const vehicleForm = reactive({ plateNumber: '', model: '', seatCount: 45 })
const tripForm = reactive({ routeId: '', vehicleId: '', departureTime: '', arrivalTime: '', baseFare: '' })
const fareRuleForm = reactive({ name: '', startDate: '', endDate: '', multiplier: 1.2, priority: 10 })
const userEditForm = reactive({ username: '', displayName: '', phone: '', role: '', isActive: true })

async function loadAll() {
  loading.value = true
  try {
    const [stationRes, routeRes, vehicleRes, tripRes, ruleRes, userRes, statsRes] = await Promise.all([
      api.get('/admin/stations'),
      api.get('/admin/routes'),
      api.get('/admin/vehicles'),
      api.get('/admin/trips'),
      api.get('/admin/fare-rules'),
      api.get('/admin/users'),
      api.get('/admin/stats'),
    ])
    stations.value = stationRes.data.data
    routes.value = routeRes.data.data
    vehicles.value = vehicleRes.data.data
    trips.value = tripRes.data.data
    fareRules.value = ruleRes.data.data
    users.value = userRes.data.data
    stats.value = statsRes.data.data
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function createStation() {
  try {
    await api.post('/admin/stations', stationForm)
    Object.assign(stationForm, { name: '', city: '', address: '' })
    ElMessage.success('站点已新增')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function createRoute() {
  try {
    await api.post('/admin/routes', routeForm)
    Object.assign(routeForm, { code: '', name: '', originStationId: '', destinationStationId: '', distanceKm: '' })
    ElMessage.success('线路已新增')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function createVehicle() {
  try {
    await api.post('/admin/vehicles', vehicleForm)
    Object.assign(vehicleForm, { plateNumber: '', model: '', seatCount: 45 })
    ElMessage.success('车辆已新增')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function createTrip() {
  try {
    await api.post('/admin/trips', tripForm)
    Object.assign(tripForm, { routeId: '', vehicleId: '', departureTime: '', arrivalTime: '', baseFare: '' })
    ElMessage.success('班次已新增')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function createFareRule() {
  try {
    await api.post('/admin/fare-rules', fareRuleForm)
    Object.assign(fareRuleForm, { name: '', startDate: '', endDate: '', multiplier: 1.2, priority: 10 })
    ElMessage.success('票价规则已新增')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function toggleUser(user) {
  try {
    await api.patch(`/admin/users/${user.id}`, { isActive: !user.isActive })
    ElMessage.success('用户状态已更新')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

function openEditUser(user) {
  editingUser.value = user
  userEditForm.username = user.username
  userEditForm.displayName = user.displayName
  userEditForm.phone = user.phone || ''
  userEditForm.role = user.role
  userEditForm.isActive = user.isActive
  userEditDialogOpen.value = true
}

async function saveUser() {
  try {
    await api.patch(`/admin/users/${editingUser.value.id}`, { ...userEditForm })
    ElMessage.success('用户信息已更新')
    userEditDialogOpen.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function deleteUser(user) {
  try {
    await ElMessageBox.confirm(
      `确认删除用户「${user.displayName}」（${user.username}）吗？该操作将一并删除其所有订单和车票数据，且不可恢复。`,
      '删除用户',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
    await api.delete(`/admin/users/${user.id}`)
    ElMessage.success('用户已删除')
    await loadAll()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message)
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="workspace">
    <section class="metric-grid">
      <div class="metric">
        <span>有效车票</span>
        <strong>{{ stats.activeTicketCount || 0 }}</strong>
      </div>
      <div class="metric">
        <span>退票</span>
        <strong>{{ stats.refundedTicketCount || 0 }}</strong>
      </div>
      <div class="metric">
        <span>换出车票</span>
        <strong>{{ stats.exchangedTicketCount || 0 }}</strong>
      </div>
      <div class="metric">
        <span>有效销售额</span>
        <strong>￥{{ Number(stats.activeSalesAmount || 0).toFixed(2) }}</strong>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>基础数据维护</h2>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="站点" name="stations">
          <div class="form-grid">
            <el-input v-model="stationForm.name" placeholder="站点名称" />
            <el-input v-model="stationForm.city" placeholder="城市" />
            <el-input v-model="stationForm.address" placeholder="地址" />
            <el-button type="primary" :icon="Plus" @click="createStation">新增站点</el-button>
          </div>
          <el-table :data="stations" :loading="loading" border style="margin-top: 14px">
            <el-table-column prop="name" label="站点" />
            <el-table-column prop="city" label="城市" width="120" />
            <el-table-column prop="address" label="地址" />
            <el-table-column prop="isActive" label="启用" width="90" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="线路" name="routes">
          <div class="form-grid">
            <el-input v-model="routeForm.code" placeholder="编码" />
            <el-input v-model="routeForm.name" placeholder="线路名称" />
            <el-select v-model="routeForm.originStationId" placeholder="出发站">
              <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
            </el-select>
            <el-select v-model="routeForm.destinationStationId" placeholder="到达站">
              <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
            </el-select>
            <el-input v-model="routeForm.distanceKm" placeholder="里程 km" />
            <el-button type="primary" :icon="Plus" @click="createRoute">新增线路</el-button>
          </div>
          <el-table :data="routes" border style="margin-top: 14px">
            <el-table-column prop="code" label="编码" width="110" />
            <el-table-column prop="name" label="线路" />
            <el-table-column prop="originStationName" label="出发站" />
            <el-table-column prop="destinationStationName" label="到达站" />
            <el-table-column prop="distanceKm" label="里程" width="100" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="车辆" name="vehicles">
          <div class="form-grid">
            <el-input v-model="vehicleForm.plateNumber" placeholder="车牌号" />
            <el-input v-model="vehicleForm.model" placeholder="车型" />
            <el-input-number v-model="vehicleForm.seatCount" :min="1" :max="80" />
            <el-button type="primary" :icon="Plus" @click="createVehicle">新增车辆</el-button>
          </div>
          <el-table :data="vehicles" border style="margin-top: 14px">
            <el-table-column prop="plateNumber" label="车牌" />
            <el-table-column prop="model" label="车型" />
            <el-table-column prop="seatCount" label="座位数" width="100" />
            <el-table-column prop="status" label="状态" width="120" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="班次" name="trips">
          <div class="form-grid">
            <el-select v-model="tripForm.routeId" placeholder="线路">
              <el-option v-for="route in routes" :key="route.id" :label="route.name" :value="route.id" />
            </el-select>
            <el-select v-model="tripForm.vehicleId" placeholder="车辆">
              <el-option v-for="vehicle in vehicles" :key="vehicle.id" :label="vehicle.plateNumber" :value="vehicle.id" />
            </el-select>
            <el-date-picker v-model="tripForm.departureTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="发车时间" />
            <el-date-picker v-model="tripForm.arrivalTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="到达时间" />
            <el-input v-model="tripForm.baseFare" placeholder="基础票价" />
            <el-button type="primary" :icon="Plus" @click="createTrip">新增班次</el-button>
          </div>
          <el-table :data="trips" border style="margin-top: 14px">
            <el-table-column prop="routeName" label="线路" />
            <el-table-column label="发车">
              <template #default="{ row }">{{ formatDateTime(row.departureTime) }}</template>
            </el-table-column>
            <el-table-column prop="plateNumber" label="车辆" width="110" />
            <el-table-column prop="remainingSeats" label="余票" width="90" />
            <el-table-column label="票价" width="100">
              <template #default="{ row }">￥{{ row.fare.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="票价规则" name="fareRules">
          <div class="form-grid">
            <el-input v-model="fareRuleForm.name" placeholder="规则名称" />
            <el-date-picker v-model="fareRuleForm.startDate" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
            <el-date-picker v-model="fareRuleForm.endDate" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
            <el-input-number v-model="fareRuleForm.multiplier" :min="0.1" :max="5" :step="0.05" />
            <el-input-number v-model="fareRuleForm.priority" :min="0" :max="99" />
            <el-button type="primary" :icon="Plus" @click="createFareRule">新增规则</el-button>
          </div>
          <el-table :data="fareRules" border style="margin-top: 14px">
            <el-table-column prop="name" label="规则" />
            <el-table-column prop="startDate" label="开始" width="120" />
            <el-table-column prop="endDate" label="结束" width="120" />
            <el-table-column prop="multiplier" label="倍率" width="100" />
            <el-table-column prop="priority" label="优先级" width="100" />
            <el-table-column prop="isActive" label="启用" width="90" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="用户" name="users">
          <el-table :data="users" border>
            <el-table-column prop="username" label="账号" />
            <el-table-column prop="displayName" label="姓名" />
            <el-table-column prop="role" label="角色" width="120" />
            <el-table-column prop="phone" label="手机号" />
            <el-table-column prop="isActive" label="启用" width="90" />
            <el-table-column label="操作" width="210" fixed="right">
              <template #default="{ row }">
                <el-button size="small" :icon="Edit" @click="openEditUser(row)">编辑</el-button>
                <el-button size="small" type="danger" :icon="Delete" @click="deleteUser(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="userEditDialogOpen" title="编辑用户" width="440">
      <el-form label-position="top">
        <el-form-item label="账号">
          <el-input v-model="userEditForm.username" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userEditForm.displayName" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="userEditForm.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userEditForm.role" style="width: 100%">
            <el-option label="旅客" value="PASSENGER" />
            <el-option label="售票员" value="STAFF" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="userEditForm.isActive" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userEditDialogOpen = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
