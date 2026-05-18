<script setup>
import { BookOpen, Users2, Target, CheckCircle2 } from 'lucide-vue-next'

const quickStats = [
  { label: 'Courses managed',    value: '5',   icon: BookOpen,     color: 'text-asi-purple', bg: 'bg-asi-purple-light' },
  { label: 'Enrolled learners',  value: '14',  icon: Users2,       color: 'text-asi-blue',   bg: 'bg-asi-blue-light'   },
  { label: 'Avg. completion',    value: '68%', icon: Target,       color: 'text-asi-red',    bg: 'bg-asi-red-light'    },
  { label: 'Certificates issued',value: '3',   icon: CheckCircle2, color: 'text-asi-orange', bg: 'bg-asi-orange-light' },
]
</script>

<template>
  <div class="min-h-screen bg-asi-surface">
    <div class="p-6 max-w-[1400px] mx-auto space-y-6">

      <!-- Hero banner -->
      <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#462C6B] via-[#7D6B9D] to-[#CA1F47] p-7 text-white shadow-xl">
        <div class="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div class="absolute bottom-0 right-24 h-32 w-32 rounded-full bg-asi-orange/20 blur-2xl" />
        <div class="relative">
          <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-white/80 ring-1 ring-white/15">
            <BookOpen :size="14" />
            Instructor portal
          </div>
          <h1 class="text-3xl font-bold tracking-tight md:text-4xl">Instructor Dashboard</h1>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-white/75">
            Manage your courses, track learner progress, and review completions.
          </p>
        </div>
      </div>

      <!-- Stats -->
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

      <!-- Placeholder -->
      <div class="widget-card text-center">
        <p class="text-sm text-asi-gray">
          Instructor-specific widgets (course list, learner activity, grading queue) will appear here.
        </p>
      </div>
    </div>
  </div>
</template>
