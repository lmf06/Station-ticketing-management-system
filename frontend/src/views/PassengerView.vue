<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search, ShoppingCart, Refresh, Switch, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, formatDateTime } from '../api'

const stations = ref([])
const trips = ref([])
const tickets = ref([])
const loadingTrips = ref(false)
const loadingTickets = ref(false)
const buyDialogOpen = ref(false)
const exchangeDialogOpen = ref(false)
const selectedTrip = ref(null)
const selectedTicket = ref(null)

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

const passengerForm = reactive({
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
  loadingTrips.value = true
  try {
    const { data } = await api.get('/trips', { params: filters })
    trips.value = data.data
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loadingTrips.value = false
  }
}

async function loadTickets() {
  loadingTickets.value = true
  try {
    const { data } = await api.get('/my/tickets')
    tickets.value = data.data
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loadingTickets.value = false
  }
}

function openBuy(trip) {
  selectedTrip.value = trip
  passengerForm.passengerName = ''
  passengerForm.passengerIdCard = ''
  buyDialogOpen.value = true
}

async function buyTicket() {
  try {
    await api.post('/orders', {
      tripId: selectedTrip.value.id,
      passengerName: passengerForm.passengerName,
      passengerIdCard: passengerForm.passengerIdCard,
    })
    ElMessage.success('购票成功')
    buyDialogOpen.value = false
    await Promise.all([loadTrips(), loadTickets()])
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function refundTicket(ticket) {
  try {
    await ElMessageBox.confirm(`确认退票 ${ticket.ticketNo}？`, '退票确认', { type: 'warning' })
    await api.post(`/tickets/${ticket.id}/refund`)
    ElMessage.success('退票成功')
    await Promise.all([loadTrips(), loadTickets()])
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
    await Promise.all([loadTrips(), loadTickets()])
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(async () => {
  await loadStations()
  await Promise.all([loadTrips(), loadTickets()])
})
</script>

<template>
  <div class="workspace">
    <section class="panel">
      <div class="panel-header">
        <h2>班次查询</h2>
        <el-button :icon="Refresh" @click="loadTrips">刷新</el-button>
      </div>
      <div class="filters">
        <el-select v-model="filters.fromStationId" placeholder="出发站">
          <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
        </el-select>
        <el-select v-model="filters.toStationId" placeholder="到达站">
          <el-option v-for="station in stations" :key="station.id" :label="station.name" :value="station.id" />
        </el-select>
        <el-date-picker v-model="filters.date" type="date" value-format="YYYY-MM-DD" placeholder="日期" />
        <el-button type="primary" :icon="Search" @click="loadTrips">查询</el-button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>可售班次</h2>
      </div>
      <el-table :data="trips" :loading="loadingTrips" border>
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
            <el-button type="primary" :icon="ShoppingCart" size="small" :disabled="row.remainingSeats <= 0" @click="openBuy(row)">购票</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>我的车票</h2>
        <el-button :icon="Refresh" @click="loadTickets">刷新</el-button>
      </div>
      <el-table :data="tickets" :loading="loadingTickets" border>
        <el-table-column prop="ticketNo" label="票号" min-width="190" />
        <el-table-column prop="routeName" label="线路" min-width="150" />
        <el-table-column label="发车时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.departureTime) }}</template>
        </el-table-column>
        <el-table-column prop="passengerName" label="乘车人" width="110" />
        <el-table-column prop="seatNumber" label="座位" width="80" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="票价" width="100">
          <template #default="{ row }">￥{{ row.fare.toFixed(2) }}</template>
        </el-table-column>
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

    <el-dialog v-model="buyDialogOpen" title="购票" width="420">
      <el-descriptions v-if="selectedTrip" :column="1" border>
        <el-descriptions-item label="线路">{{ selectedTrip.routeName }}</el-descriptions-item>
        <el-descriptions-item label="发车">{{ formatDateTime(selectedTrip.departureTime) }}</el-descriptions-item>
        <el-descriptions-item label="票价">￥{{ selectedTrip.fare.toFixed(2) }}</el-descriptions-item>
      </el-descriptions>
      <el-form label-position="top" style="margin-top: 14px">
        <el-form-item label="乘车人">
          <el-input v-model="passengerForm.passengerName" placeholder="默认使用本人信息" />
        </el-form-item>
        <el-form-item label="证件号">
          <el-input v-model="passengerForm.passengerIdCard" placeholder="默认使用本人证件" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="buyDialogOpen = false">取消</el-button>
        <el-button type="primary" :icon="ShoppingCart" @click="buyTicket">确认购票</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="exchangeDialogOpen" title="换票" width="460">
      <el-form label-position="top">
        <el-form-item label="新班次">
          <el-select v-model="exchangeForm.newTripId" placeholder="选择新班次" style="width: 100%">
            <el-option
              v-for="trip in trips.filter((item) => item.id !== selectedTicket?.tripId && item.remainingSeats > 0)"
              :key="trip.id"
              :label="`${trip.routeName} ${formatDateTime(trip.departureTime)} ￥${trip.fare.toFixed(2)}`"
              :value="trip.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exchangeDialogOpen = false">取消</el-button>
        <el-button type="primary" :icon="Switch" :disabled="!exchangeForm.newTripId" @click="exchangeTicket">确认换票</el-button>
      </template>
    </el-dialog>
  </div>
</template>
