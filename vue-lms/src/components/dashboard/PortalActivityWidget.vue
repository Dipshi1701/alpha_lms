<script setup>
import { ref, computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import PortalActivityChart from '../charts/PortalActivityChart.vue'

const periods = ['Today', 'Yesterday', 'Last 7 days', 'Last 30 days']

const generateData = (period) => {
  const hours = ['00:00','02:00','04:00','06:00','08:00','10:00','12:00','14:00','16:00','18:00','20:00','22:00','23:59']
  if (period === 'Yesterday') {
    return hours.map((h, i) => ({
      time: h,
      logins: i === 6 ? 1 : 0,
      completions: i === 8 ? 1 : 0
    }))
  }
  return hours.map((h) => ({ time: h, logins: 0, completions: 0 }))
}

const period = ref('Yesterday')
const open = ref(false)

const data = computed(() => generateData(period.value))
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold text-gray-700">
        Portal activity
      </h3>
      <div class="relative">
        <button
          class="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-100 transition-colors"
          @click="open = !open"
        >
          {{ period }}
          <ChevronDown
            :size="14"
            class="transition-transform"
            :class="open ? 'rotate-180' : ''"
          />
        </button>
        <div
          v-if="open"
          class="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 min-w-[130px]"
        >
          <button
            v-for="p in periods"
            :key="p"
            class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
            :class="p === period ? 'text-blue-600 font-medium' : 'text-gray-700'"
            @click="period = p; open = false"
          >
            {{ p }}
          </button>
        </div>
      </div>
    </div>

    <div class="h-48">
      <PortalActivityChart :data-points="data" />
    </div>

    <div class="flex items-center gap-5 mt-3">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-blue-500" />
        <span class="text-xs text-gray-500">Logins</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-green-500" />
        <span class="text-xs text-gray-500">Course completions</span>
      </div>
    </div>
  </div>
</template>


