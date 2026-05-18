<script setup>
import { Users, BookOpen, TrendingUp, Settings2 } from 'lucide-vue-next'
import OverviewWidget from './OverviewWidget.vue'
import CoursesProgressWidget from './CoursesProgressWidget.vue'
import PortalActivityWidget from './PortalActivityWidget.vue'
import QuickActionsWidget from './QuickActionsWidget.vue'
import UsersWidget from './UsersWidget.vue'
import TimelineWidget from './TimelineWidget.vue'

const quickStats = [
  { label: 'Total users',      value: '128',  icon: Users,      color: 'text-asi-purple',   bg: 'bg-asi-purple-light' },
  { label: 'Active courses',   value: '34',   icon: BookOpen,   color: 'text-asi-blue',     bg: 'bg-asi-blue-light'   },
  { label: 'Completion rate',  value: '74%',  icon: TrendingUp, color: 'text-asi-red',      bg: 'bg-asi-red-light'    },
  { label: 'System settings',  value: '12',   icon: Settings2,  color: 'text-asi-orange',   bg: 'bg-asi-orange-light' },
]
</script>

<template>
  <div class="min-h-screen bg-asi-surface">
    <div class="p-6 max-w-[1400px] mx-auto space-y-6">

      <!-- ── Page header ──────────────────────────────────────────────────── -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-asi-black">Dashboard</h1>
          <p class="text-sm text-asi-gray mt-0.5">Overview of your portal's activity, users and course progress.</p>
        </div>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article
          v-for="stat in quickStats"
          :key="stat.label"
          class="widget-card"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-asi-gray">{{ stat.label }}</p>
              <p class="mt-2 text-2xl font-bold text-asi-black">{{ stat.value }}</p>
            </div>
            <div :class="['rounded-2xl p-3', stat.bg]">
              <component :is="stat.icon" :size="22" :class="stat.color" />
            </div>
          </div>
        </article>
      </div>

      <!-- Widgets grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <OverviewWidget />
        <CoursesProgressWidget />
        <PortalActivityWidget />
        <QuickActionsWidget />
        <UsersWidget />
        <TimelineWidget />
      </div>

    </div>
  </div>
</template>
