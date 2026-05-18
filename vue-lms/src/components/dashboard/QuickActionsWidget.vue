<script setup>
import { UserPlus, BookPlus, Settings, Users2, BarChart2 } from 'lucide-vue-next'

const actions = [
  { label: 'Add user',        icon: UserPlus,  color: 'text-asi-purple',  bg: 'bg-asi-purple-light', hover: 'group-hover:bg-asi-purple-light group-hover:text-asi-purple'  },
  { label: 'Add course',      icon: BookPlus,  color: 'text-asi-blue',    bg: 'bg-asi-blue-light',   hover: 'group-hover:bg-asi-blue-light group-hover:text-asi-blue'      },
  { label: 'Portal settings', icon: Settings,  color: 'text-asi-lavender',bg: 'bg-asi-purple-light', hover: 'group-hover:bg-asi-purple-light group-hover:text-asi-lavender'},
  { label: 'Add group',       icon: Users2,    color: 'text-asi-orange',  bg: 'bg-asi-orange-light', hover: 'group-hover:bg-asi-orange-light group-hover:text-asi-orange'  },
  { label: 'Custom reports',  icon: BarChart2, color: 'text-asi-red',     bg: 'bg-asi-red-light',    hover: 'group-hover:bg-asi-red-light group-hover:text-asi-red'        },
]
</script>

<template>
  <div class="widget-card">
    <h3 class="text-base font-semibold text-asi-black mb-4">Quick actions</h3>
    <div class="space-y-1">
      <button
        v-for="action in actions"
        :key="action.label"
        class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-asi-gray hover:bg-asi-surface transition-all group"
      >
        <div :class="['w-7 h-7 rounded-lg bg-asi-surface flex items-center justify-center transition-colors', action.hover]">
          <component :is="action.icon" :size="15" :class="['transition-colors', action.color]" />
        </div>
        <span class="font-medium group-hover:text-asi-black transition-colors">{{ action.label }}</span>
      </button>
    </div>
  </div>
</template>
