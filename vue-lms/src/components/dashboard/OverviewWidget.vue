<script setup>
import { Users, BookOpen, Users2, Clock, TrendingUp } from 'lucide-vue-next'

const stats = [
  { label: 'Active users', value: 2, icon: Users },
  { label: 'Assigned courses', value: 1, icon: BookOpen },
  { label: 'Groups', value: 0, icon: Users2 },
  { label: 'Training time', value: '0h 0m', icon: Clock },
  { label: 'Completion rate', value: '100.00%', icon: TrendingUp }
]
</script>

<template>
  <div class="widget-card">
    <h3 class="text-base font-semibold text-gray-700 mb-4">
      Overview
    </h3>
    <div class="space-y-3">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="flex items-center justify-between py-1"
      >
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <component :is="stat.icon" :size="15" class="text-gray-500" />
          </div>
          <span class="text-sm text-gray-600">
            {{ stat.label }}
          </span>
        </div>
        <span class="text-sm font-semibold text-gray-800">
          {{ stat.value }}
        </span>
      </div>
    </div>
  </div>
</template>

