<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search, ShoppingCart, Refresh, Switch, Close, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, formatDateTime } from '../api'

const stations = ref([])
const trips = ref([])
const tickets = ref([])
const stats = ref({})
const selectedTrip = ref(null)
const sellDialogOpen = ref(false)
const exchangeDialogOpen = ref(false)
const selectedTicket = ref(null)
const loading = ref(false)

function defaultTravelDate() {
  const day = new Date()
  day.setDate(day.getDate() + 1)
  return day.toISOString().slice(0, 10)
}

const filters = reactive({
  fromStationId: '',
  toStationId: '',
  date: defaultTravelDate(),
})

const sellForm = reactive({
  passengerName: '',
  passengerIdCard: '',
})

const exchangeForm = reactive({
  newTripId: '',
})

async function loadStations() {
  const { data } = await api.get('/stations')
  stations.value = data.data
  const defaultOrigin = stations.value.find((station) => station.name.includes('杭州')) || stations.value[0]
  const defaultDestination = stations.value.find((station) => station.name.includes('宁波')) || stations.value[1]
  if (!filters.fromStationId && defaultOrigin) filters.fromStationId = defaultOrigin.id
  if (!filters.toStationId && defaultDestination) filters.toStationId = defaultDestination.id
}

async function loadTrips() {
  const { data } = await api.get('/trips', { params: filters })
  trips.value = data.data
}

async function loadTickets() {
  const { data } = await api.get('/admin/orders')
  tickets.value = data.data
}

async function loadStats() {
  const { data } = await api.get('/admin/stats')
  stats.value = data.data
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([loadTrips(), loadTickets(), loadStats()])
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function openSell(trip) {
  selectedTrip.value = trip
  sellForm.passengerName = ''
  sellForm.passengerIdCard = ''
  sellDialogOpen.value = true
}

async function sellTicket() {
  try {
    await api.post('/orders', {
      tripId: selectedTrip.value.id,
      passengerName: sellForm.passengerName,
      passengerIdCard: sellForm.passengerIdCard,
    })
    ElMessage.success('售票成功')
    sellDialogOpen.value = false
    await refreshAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function refundTicket(ticket) {
  try {
    await ElMessageBox.confirm(`确认退票 ${ticket.ticketNo}？`, '退票确认', { type: 'warning' })
    await api.post(`/tickets/${ticket.id}/refund`)
    ElMessage.success('退票成功')
    await refreshAll()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message)
  }
}

function openExchange(ticket) {
  selectedTicket.value = ticket
  exchangeForm.newTripId = ''
  exchangeDialogOpen.value = true
}

async function exchangeTicket() {
  try {
    await api.post(`/tickets/${selectedTicket.value.id}/exchange`, { newTripId: exchangeForm.newTripId })
    ElMessage.success('换票成功')
    exchangeDialogOpen.value = false
    await refreshAll()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(async () => {
  await loadStations()
  await refreshAll()
})
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
        <h2>窗口售票</h2>
        <el-button :icon="Refresh" @click="refreshAll">刷新</el-button>
      </div>
      <div class="filters">
        <el-select v-model="filters.fromStationId" placeholder="出发站">
          <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
        </el-select>
        <el-select v-model="filters.toStationId" placeholder="到达站">
          <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
        </el-select>
        <el-date-picker v-model="filters.date" type="date" value-format="YYYY-MM-DD" placeholder="日期" />
        <el-button type="primary" :icon="Search" @click="refreshAll">查询</el-button>
      </div>
      <el-table :data="trips" :loading="loading" border style="margin-top: 14px">
        <el-table-column prop="routeName" label="线路" min-width="140" />
        <el-table-column label="区间" min-width="220">
          <template #default="{ row }">{{ row.originStationName }} → {{ row.destinationStationName }}</template>
        </el-table-column>
        <el-table-column label="发车时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.departureTime) }}</template>
        </el-table-column>
        <el-table-column prop="plateNumber" label="车辆" width="95" />
        <el-table-column prop="remainingSeats" label="余票" width="70" />
        <el-table-column label="票价" width="90">
          <template #default="{ row }">￥{{ row.fare.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="105">
          <template #default="{ row }">
            <el-button type="primary" :icon="ShoppingCart" size="small" :disabled="row.remainingSeats <= 0" @click="openSell(row)">售票</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>票务办理</h2>
        <el-button :icon="TrendCharts" @click="loadStats">统计</el-button>
      </div>
      <el-table :data="tickets" border>
        <el-table-column prop="ticketNo" label="票号" min-width="190" />
        <el-table-column prop="routeName" label="线路" min-width="150" />
        <el-table-column label="发车时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.departureTime) }}</template>
        </el-table-column>
        <el-table-column prop="passengerName" label="乘车人" width="110" />
        <el-table-column prop="seatNumber" label="座位" width="80" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button :icon="Switch" size="small" :disabled="row.status !== 'ACTIVE'" @click="openExchange(row)">换票</el-button>
              <el-button :icon="Close" size="small" type="danger" :disabled="row.status !== 'ACTIVE'" @click="refundTicket(row)">退票</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="sellDialogOpen" title="窗口售票" width="420">
      <el-form label-position="top">
        <el-form-item label="乘车人">
          <el-input v-model="sellForm.passengerName" />
        </el-form-item>
        <el-form-item label="证件号">
          <el-input v-model="sellForm.passengerIdCard" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sellDialogOpen = false">取消</el-button>
        <el-button type="primary" :icon="ShoppingCart" @click="sellTicket">出票</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="exchangeDialogOpen" title="换票" width="460">
      <el-select v-model="exchangeForm.newTripId" placeholder="选择新班次" style="width: 100%">
        <el-option
          v-for="trip in trips.filter((item) => item.id !== selectedTicket?.tripId && item.remainingSeats > 0)"
          :key="trip.id"
          :label="`${trip.routeName} ${formatDateTime(trip.departureTime)} ￥${trip.fare.toFixed(2)}`"
          :value="trip.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="exchangeDialogOpen = false">取消</el-button>
        <el-button type="primary" :icon="Switch" :disabled="!exchangeForm.newTripId" @click="exchangeTicket">确认换票</el-button>
      </template>
    </el-dialog>
  </div>
</template>
