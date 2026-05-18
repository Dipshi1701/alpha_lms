<script setup>
import { ChevronRight } from 'lucide-vue-next'
import CoursesDonutChart from '../charts/CoursesDonutChart.vue'

// ASI brand-aligned chart colors
const data = [
  { name: 'Completed',   value: 100, color: '#462C6B' },
  { name: 'In progress', value: 30,  color: '#F26524' },
  { name: 'Not started', value: 20,  color: '#E8E2F0' },
  { name: 'Not passed',  value: 2,   color: '#CA1F47' },
]

const total = data.reduce((sum, d) => sum + d.value, 0)
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-1 cursor-pointer group">
        <h3 class="text-base font-semibold text-asi-black group-hover:text-asi-purple transition-colors">
          Courses' progress status
        </h3>
        <ChevronRight :size="16" class="text-asi-gray group-hover:text-asi-lavender transition-colors" />
      </div>
      <span class="text-lg font-bold text-asi-black">{{ total }}</span>
    </div>

    <div class="h-44 flex items-center justify-center">
      <CoursesDonutChart :slices="data" />
    </div>

    <div class="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-1">
      <div v-for="item in data" :key="item.name" class="flex items-center gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: item.color }" />
        <span class="text-xs text-asi-gray">{{ item.name }}</span>
      </div>
    </div>
  </div>
</template>
