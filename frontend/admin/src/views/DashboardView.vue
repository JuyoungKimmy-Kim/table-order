<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import TableCard from '../components/TableCard.vue'
import TableFilter from '../components/TableFilter.vue'
import OrderDetailModal from '../components/OrderDetailModal.vue'

const dashboard = useDashboardStore()
const selectedOrderId = ref(null)

onMounted(() => { dashboard.init() })
onUnmounted(() => { dashboard.disconnect() })

function openOrder(orderId) { selectedOrderId.value = orderId }
function closeOrder() { selectedOrderId.value = null }
</script>

<template>
  <div class="dashboard">
    <div class="bar">
      <h1>실시간 주문 모니터링</h1>
      <span class="conn" :class="dashboard.connection">{{ dashboard.connection }}</span>
    </div>
    <TableFilter />
    <div class="grid">
      <TableCard
        v-for="t in dashboard.visibleTables"
        :key="t.table_id"
        :card="t"
        @open-order="openOrder"
      />
    </div>
    <OrderDetailModal
      v-if="selectedOrderId"
      :order-id="selectedOrderId"
      @close="closeOrder"
    />
  </div>
</template>

<style scoped>
.bar { display: flex; align-items: center; gap: 12px; }
.bar h1 { font-size: 18px; }
.conn { font-size: 12px; padding: 2px 8px; border-radius: 10px; background: #e5e7eb; }
.conn.open { background: #dcfce7; color: #166534; }
.conn.reconnecting { background: #fef3c7; color: #92400e; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px; margin-top: 12px; }
</style>
