<script setup>
import { ChevronRight } from 'lucide-vue-next'

const data = [
  { name: 'Admins', value: 1, color: '#1e40af' },
  { name: 'Instructors', value: 0, color: '#3b82f6' },
  { name: 'Learners', value: 1, color: '#1e3a5f' }
]

const chartData = data.filter(d => d.value > 0)
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-1 cursor-pointer group">
        <h3 class="text-base font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
          Users
        </h3>
        <ChevronRight :size="16" class="text-gray-400 group-hover:text-blue-500 transition-colors" />
      </div>
      <span class="text-lg font-bold text-gray-700">
        2
      </span>
    </div>

    <!-- Simple donut-style chart using CSS gradients -->
    <div class="flex items-center justify-center h-44">
      <div class="relative w-32 h-32">
        <div
          class="w-full h-full rounded-full"
          :style="{
            background: `conic-gradient(
              ${chartData[0]?.color || '#1e40af'} 0 50%,
              ${chartData[1]?.color || '#1e3a5f'} 50% 100%
            )`
          }"
        />
        <div class="absolute inset-5 bg-white rounded-full flex items-center justify-center">
          <span class="text-base font-semibold text-gray-700">
            2
          </span>
        </div>
      </div>
    </div>

    <div class="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
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

