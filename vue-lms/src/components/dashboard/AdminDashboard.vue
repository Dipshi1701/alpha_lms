<script setup>
import { Wand2, LayoutDashboard, ExternalLink } from 'lucide-vue-next'
import OverviewWidget from './OverviewWidget.vue'
import CoursesProgressWidget from './CoursesProgressWidget.vue'
import PortalActivityWidget from './PortalActivityWidget.vue'
import QuickActionsWidget from './QuickActionsWidget.vue'
import UsersWidget from './UsersWidget.vue'
import TimelineWidget from './TimelineWidget.vue'
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <Wand2 :size="22" class="text-orange-400" />
        <h1 class="text-xl font-bold text-gray-800">
          Welcome to Alpha Learn, dipshi!
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all shadow-sm"
        >
          <LayoutDashboard :size="15" />
          <span>Add widgets</span>
        </button>
        <button
          class="p-2 text-gray-500 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all shadow-sm"
        >
          <ExternalLink :size="15" />
        </button>
      </div>
    </div>

    <!-- Dashboard Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <OverviewWidget />
      <CoursesProgressWidget />
      <PortalActivityWidget />
      <QuickActionsWidget />
      <UsersWidget />
      <TimelineWidget />
    </div>
  </div>
</template>

