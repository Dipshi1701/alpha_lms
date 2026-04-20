<script setup>
import { ChevronRight } from 'lucide-vue-next'
import CoursesDonutChart from '../charts/CoursesDonutChart.vue'

const data = [
  { name: 'Completed', value: 100, color: '#4ade80' },
  { name: 'In progress', value: 30, color: '#fb923c' },
  { name: 'Not started', value: 20, color: '#d1d5db' },
  { name: 'Not passed', value: 2, color: '#f87171' }
]

const total = data.reduce((sum, d) => sum + d.value, 0)
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-1 cursor-pointer group">
        <h3 class="text-base font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
          Courses' progress status
        </h3>
        <ChevronRight :size="16" class="text-gray-400 group-hover:text-blue-500 transition-colors" />
      </div>
      <span class="text-lg font-bold text-gray-700">
        {{ total }}
      </span>
    </div>

    <div class="h-44 flex items-center justify-center">
      <CoursesDonutChart :slices="data" />
    </div>

    <div class="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-1">
      <div
        v-for="item in data"
        :key="item.name"
        class="flex items-center gap-1.5"
      >
        <div
          class="w-2.5 h-2.5 rounded-full"
          :style="{ backgroundColor: item.color }"
        />
        <span class="text-xs text-gray-500">
          {{ item.name }}
        </span>
      </div>
    </div>
  </div>
</template>


