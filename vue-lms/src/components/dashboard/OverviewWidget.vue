<script setup>
import { Users, BookOpen, Users2, Clock, TrendingUp } from 'lucide-vue-next'

const stats = [
  { label: 'Active users',    value: 2,         icon: Users,      color: 'text-asi-purple',  bg: 'bg-asi-purple-light' },
  { label: 'Assigned courses',value: 1,         icon: BookOpen,   color: 'text-asi-blue',    bg: 'bg-asi-blue-light'   },
  { label: 'Groups',          value: 0,         icon: Users2,     color: 'text-asi-orange',  bg: 'bg-asi-orange-light' },
  { label: 'Training time',   value: '0h 0m',   icon: Clock,      color: 'text-asi-lavender',bg: 'bg-asi-purple-light' },
  { label: 'Completion rate', value: '100.00%', icon: TrendingUp, color: 'text-asi-red',     bg: 'bg-asi-red-light'    },
]
</script>

<template>
  <div class="widget-card">
    <h3 class="text-base font-semibold text-asi-black mb-4">Overview</h3>
    <div class="space-y-3">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="flex items-center justify-between py-1"
      >
        <div class="flex items-center gap-3">
          <div :class="['w-8 h-8 rounded-xl flex items-center justify-center', stat.bg]">
            <component :is="stat.icon" :size="15" :class="stat.color" />
          </div>
          <span class="text-sm text-asi-gray">{{ stat.label }}</span>
        </div>
        <span class="text-sm font-semibold text-asi-black">{{ stat.value }}</span>
      </div>
    </div>
  </div>
</template>
