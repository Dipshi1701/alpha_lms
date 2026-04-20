<script setup>
import { UserPlus, BookPlus, Settings, Users2, BarChart2 } from 'lucide-vue-next'

const actions = [
  { label: 'Add user', icon: UserPlus },
  { label: 'Add course', icon: BookPlus },
  { label: 'Portal settings', icon: Settings },
  { label: 'Add group', icon: Users2 },
  { label: 'Custom reports', icon: BarChart2 }
]
</script>

<template>
  <div class="widget-card">
    <h3 class="text-base font-semibold text-gray-700 mb-4">
      Quick actions
    </h3>
    <div class="space-y-1">
      <button
        v-for="action in actions"
        :key="action.label"
        class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-all group"
      >
        <div class="w-7 h-7 rounded-lg bg-gray-100 group-hover:bg-blue-50 flex items-center justify-center transition-colors">
          <component :is="action.icon" :size="15" class="text-gray-500 group-hover:text-blue-500 transition-colors" />
        </div>
        <span class="font-medium">
          {{ action.label }}
        </span>
      </button>
    </div>
  </div>
</template>

