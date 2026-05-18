<script setup>
import { ChevronRight } from 'lucide-vue-next'

// ASI brand colors for user role segments
const data = [
  { name: 'Admins',      value: 1, color: '#462C6B' },
  { name: 'Instructors', value: 0, color: '#F26524' },
  { name: 'Learners',    value: 1, color: '#4890C0' },
]

const chartData = data.filter(d => d.value > 0)
</script>

<template>
  <div class="widget-card">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-1 cursor-pointer group">
        <h3 class="text-base font-semibold text-asi-black group-hover:text-asi-purple transition-colors">
          Users
        </h3>
        <ChevronRight :size="16" class="text-asi-gray group-hover:text-asi-lavender transition-colors" />
      </div>
      <span class="text-lg font-bold text-asi-black">2</span>
    </div>

    <div class="flex items-center justify-center h-44">
      <div class="relative w-32 h-32">
        <div
          class="w-full h-full rounded-full"
          :style="{
            background: `conic-gradient(
              ${chartData[0]?.color || '#462C6B'} 0 50%,
              ${chartData[1]?.color || '#4890C0'} 50% 100%
            )`
          }"
        />
        <div class="absolute inset-5 bg-white rounded-full flex items-center justify-center shadow-inner">
          <span class="text-base font-semibold text-asi-black">2</span>
        </div>
      </div>
    </div>

    <div class="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
      <div v-for="item in data" :key="item.name" class="flex items-center gap-1.5">
        <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: item.color }" />
        <span class="text-xs text-asi-gray">{{ item.name }}</span>
      </div>
    </div>
  </div>
</template>
