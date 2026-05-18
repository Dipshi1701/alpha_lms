<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronRight, Pencil, MessageSquare, Clock,
  FileCheck, BarChart2, Calendar, BookOpen,
} from 'lucide-vue-next'
import logo1 from '../../assets/logo1.jpg'
import logo2 from '../../assets/logo2.jpg'
import logo3 from '../../assets/logo3.jpg'
import logo4 from '../../assets/logo4.jpg'
import CoursesDonutChart from '../charts/CoursesDonutChart.vue'
import { useRoleStore } from '../../stores/roleStore'
import { fetchMyCoursesLearner, fetchMyProgress } from '../../modules/courses/service'

const router = useRouter()
const { state } = useRoleStore()

const learnerName = computed(() =>
  state.user?.full_name || state.user?.name || state.user?.email?.split('@')[0] || 'Learner'
)

// ── Data ─────────────────────────────────────────────────────────────────────
const courses = ref([])
const progressMap = ref({})
const loading = ref(true)

async function load() {
  try {
    const [courseList, progress] = await Promise.all([
      fetchMyCoursesLearner(),
      fetchMyProgress().catch(() => ({})),
    ])
    courses.value = courseList
    progressMap.value = progress || {}
  } catch {
    // silently fail — show zeros
  } finally {
    loading.value = false
  }
}

onMounted(load)

function getCourseProgress(courseId) {
  return progressMap.value[String(courseId)] || { lesson_status: 'not attempted', progress_percent: 0 }
}

// ── Stats ─────────────────────────────────────────────────────────────────────
const completedCount = computed(() =>
  courses.value.filter(c => {
    const s = getCourseProgress(c.id).lesson_status
    return s === 'completed' || s === 'passed'
  }).length
)
const inProgressCount = computed(() =>
  courses.value.filter(c => getCourseProgress(c.id).lesson_status === 'incomplete').length
)
const notStartedCount = computed(() =>
  courses.value.filter(c => getCourseProgress(c.id).lesson_status === 'not attempted').length
)
const failedCount = computed(() =>
  courses.value.filter(c => getCourseProgress(c.id).lesson_status === 'failed').length
)
const completionRate = computed(() => {
  if (!courses.value.length) return '0.00%'
  return ((completedCount.value / courses.value.length) * 100).toFixed(2) + '%'
})

// ── Recent (most progress first) ─────────────────────────────────────────────
const recentCourses = computed(() =>
  [...courses.value]
    .sort((a, b) => getCourseProgress(b.id).progress_percent - getCourseProgress(a.id).progress_percent)
    .slice(0, 4)
)

const CARD_LOGOS = [logo1, logo2, logo3, logo4]

function cardLogo(idx) {
  return CARD_LOGOS[idx % CARD_LOGOS.length]
}

// ── Courses donut slices (same shape as CoursesProgressWidget) ────────────
const courseSlices = computed(() => [
  { name: 'Completed',   value: completedCount.value,   color: '#462C6B' },
  { name: 'In progress', value: inProgressCount.value,  color: '#F26524' },
  { name: 'Not started', value: notStartedCount.value,  color: '#E8E2F0' },
  { name: 'Not passed',  value: failedCount.value,       color: '#CA1F47' },
])

// ── Today ─────────────────────────────────────────────────────────────────
const todayStr = new Date().toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })

// ── Navigation ─────────────────────────────────────────────────────────────
function goToCourses() { router.push('/courses') }
function openCourse(courseId) {
  router.push({ name: 'course-player', params: { courseId: String(courseId) } })
}
</script>

<template>
  <div class="min-h-screen bg-[#F5F5F5] p-5 sm:p-6">
    <div class="max-w-[1200px] mx-auto space-y-5">

      <!-- ── Page header ──────────────────────────────────────────────────── -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-asi-black">Welcome, {{ learnerName }}!</h1>
          <p class="text-sm text-asi-gray mt-0.5">Here's a summary of your learning activity.</p>
        </div>
      </div>

      <!-- ── Recent course activity ─────────────────────────────────────── -->
      <div class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-[#F0EDF6]">
          <button
            class="flex items-center gap-1.5 text-sm font-bold text-[#231F20] hover:text-[#462C6B] transition-colors"
            @click="goToCourses"
          >
            Recent course activity
            <ChevronRight :size="16" />
          </button>
          <span v-if="!loading && courses.length" class="text-xs text-[#67686B] font-medium">{{ courses.length }} course{{ courses.length > 1 ? 's' : '' }}</span>
        </div>

        <!-- Loading skeletons -->
        <div v-if="loading" class="flex gap-4 p-5">
          <div
            v-for="i in 4" :key="i"
            class="shrink-0 w-60 rounded-2xl overflow-hidden border border-[#E8E2F0]"
          >
            <div class="h-40 bg-[#F0EDF6] animate-pulse" />
            <div class="p-3 space-y-2">
              <div class="h-3 rounded-full bg-[#F0EDF6] animate-pulse w-4/5" />
              <div class="h-2 rounded-full bg-[#F0EDF6] animate-pulse w-full" />
            </div>
          </div>
        </div>

        <!-- No courses -->
        <div v-else-if="courses.length === 0" class="flex flex-col items-center justify-center py-14 text-center px-6">
          <div class="w-12 h-12 rounded-xl bg-[#F0EDF6] flex items-center justify-center mb-3">
            <BookOpen :size="20" class="text-[#462C6B]" />
          </div>
          <p class="text-sm font-semibold text-[#231F20]">No courses assigned yet</p>
          <p class="text-xs text-[#67686B] mt-1">Your instructor will assign courses here.</p>
        </div>

        <!-- Course cards -->
        <div v-else class="flex gap-4 p-5 overflow-x-auto" style="scrollbar-width:thin">
          <div
            v-for="(course, idx) in recentCourses"
            :key="course.id"
            class="shrink-0 w-60 rounded-2xl overflow-hidden border border-[#E8E2F0] cursor-pointer hover:shadow-lg hover:border-[#7D6B9D]/40 transition-all duration-200 group bg-white flex flex-col"
            @click="openCourse(course.id)"
          >
            <!-- Logo thumbnail -->
            <div class="h-40 relative overflow-hidden bg-[#231F20]">
              <img :src="cardLogo(idx)" :alt="course.title" class="w-full h-full object-cover opacity-90" />
              <!-- Category chip top-left -->
              <span
                v-if="course.category"
                class="absolute top-2 left-2 text-[9px] font-bold px-2 py-0.5 rounded-full bg-black/40 text-white/90 backdrop-blur-sm leading-tight"
              >
                {{ course.category }}
              </span>
            </div>

            <!-- Card body -->
            <div class="p-3 flex flex-col flex-1">
              <p class="text-xs font-bold text-[#231F20] line-clamp-2 leading-snug mb-2 group-hover:text-[#462C6B] transition-colors">
                {{ course.title }}
              </p>
              <!-- Progress row -->
              <div class="mt-auto flex items-center gap-2">
                <div class="flex-1 h-1.5 rounded-full bg-[#F0EDF6] overflow-hidden">
                  <div
                    class="h-full rounded-full bg-gradient-to-r from-[#462C6B] to-[#CA1F47] transition-all"
                    :style="{ width: `${getCourseProgress(course.id).progress_percent}%` }"
                  />
                </div>
                <span class="text-[10px] font-bold text-[#462C6B]">
                  {{ getCourseProgress(course.id).progress_percent }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Row 2: Overview + Today ────────────────────────────────────── -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">

        <!-- Overview -->
        <div class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm p-5">
          <h2 class="text-sm font-bold text-[#231F20] mb-4">Overview</h2>
          <div class="space-y-0">
            <div v-for="(row, i) in [
              { icon: Pencil,       label: 'Completed assignments', value: completedCount },
              { icon: MessageSquare, label: 'Submitted comments',   value: 0 },
              { icon: Clock,        label: 'Total training time',   value: '—' },
              { icon: FileCheck,    label: 'Passed tests',          value: completedCount },
              { icon: BarChart2,    label: 'Completion rate',       value: completionRate },
            ]" :key="i">
              <div class="flex items-center gap-3 py-3">
                <component :is="row.icon" :size="15" class="text-[#67686B] shrink-0" />
                <span class="flex-1 text-sm text-[#67686B]">{{ row.label }}</span>
                <span v-if="loading && i >= 0" class="inline-block w-8 h-3.5 rounded bg-[#F0EDF6] animate-pulse" />
                <span v-else class="text-sm font-bold text-[#231F20]">{{ row.value }}</span>
              </div>
              <div v-if="i < 4" class="h-px bg-[#F7F5FA]" />
            </div>
          </div>
        </div>
 <!-- Don't miss -->
        <div class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm p-5">
          <h2 class="text-sm font-bold text-[#231F20] mb-4">Don't miss</h2>

          <div v-if="loading" class="space-y-3.5">
            <div v-for="i in 4" :key="i" class="h-3.5 rounded-full bg-[#F0EDF6] animate-pulse" :style="{ width: (55 + i * 9) + '%' }" />
          </div>

          <ul v-else class="space-y-3 text-sm text-[#67686B]">
            <li class="flex items-start gap-2.5">
              <span class="mt-2 w-1.5 h-1.5 rounded-full bg-[#231F20] shrink-0" />
              <span>
                You have no courses expiring soon.
                <button class="text-[#462C6B] font-semibold hover:underline ml-0.5" @click="goToCourses">Go to courses</button>
              </span>
            </li>
            <li v-if="inProgressCount > 0" class="flex items-start gap-2.5">
              <span class="mt-2 w-1.5 h-1.5 rounded-full bg-[#F26524] shrink-0" />
              <span>
                You have <strong class="text-[#231F20]">{{ inProgressCount }}</strong> course{{ inProgressCount > 1 ? 's' : '' }} in progress.
                <button class="text-[#462C6B] font-semibold hover:underline ml-0.5" @click="goToCourses">Continue learning</button>
              </span>
            </li>
            <li v-if="notStartedCount > 0" class="flex items-start gap-2.5">
              <span class="mt-2 w-1.5 h-1.5 rounded-full bg-[#9B92B8] shrink-0" />
              <span>
                <strong class="text-[#231F20]">{{ notStartedCount }}</strong> course{{ notStartedCount > 1 ? 's' : '' }} not started yet.
                <button class="text-[#462C6B] font-semibold hover:underline ml-0.5" @click="goToCourses">Start now</button>
              </span>
            </li>
          </ul>
        </div>
      
      </div>

      <!-- ── Row 3: My Courses chart + Don't miss ───────────────────────── -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">

        <!-- Courses' progress status — mirrors CoursesProgressWidget -->
        <div class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm p-5">
          <!-- Header -->
          <div class="flex items-center justify-between mb-2">
            <button
              class="flex items-center gap-1 cursor-pointer group"
              @click="goToCourses"
            >
              <h3 class="text-base font-semibold text-asi-black group-hover:text-asi-purple transition-colors">
                Courses' progress status
              </h3>
              <ChevronRight :size="16" class="text-asi-gray group-hover:text-asi-lavender transition-colors" />
            </button>
            <span class="text-lg font-bold text-asi-black">{{ courses.length }}</span>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="h-44 flex items-center justify-center">
            <div class="w-36 h-36 rounded-full border-[14px] border-[#F0EDF6] animate-pulse" />
          </div>

          <!-- Empty state -->
          <div v-else-if="courses.length === 0" class="h-44 flex flex-col items-center justify-center">
            <div class="w-32 h-32 rounded-full border-[14px] border-[#F0EDF6]" />
            <p class="text-xs text-asi-gray mt-4">No courses assigned</p>
          </div>

          <!-- Chart — same as admin CoursesProgressWidget -->
          <template v-else>
            <div class="h-44 flex items-center justify-center">
              <CoursesDonutChart :slices="courseSlices" />
            </div>
            <div class="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-1">
              <div v-for="item in courseSlices" :key="item.name" class="flex items-center gap-1.5">
                <div class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: item.color }" />
                <span class="text-xs text-asi-gray">{{ item.name }}</span>
              </div>
            </div>
          </template>
        </div>

          <!-- Today -->
        <div class="bg-white rounded-2xl border border-[#E8E2F0] shadow-sm p-5">
          <h2 class="text-sm font-bold text-[#231F20] mb-1">Today</h2>
          <p class="text-xs text-[#67686B] mb-4">{{ todayStr }}</p>
          <div class="flex flex-col items-center justify-center py-10 text-center">
            <div class="w-14 h-14 rounded-2xl bg-[#F0EDF6] flex items-center justify-center mb-4 shadow-sm">
              <Calendar :size="26" class="text-[#462C6B]" />
            </div>
            <p class="text-sm font-semibold text-[#231F20]">Nothing happening today</p>
            <p class="text-xs text-[#67686B] mt-1.5 max-w-[220px] leading-relaxed">
              No courses deadlines scheduled for today.
            </p>
          </div>
        </div>

       
      </div>

    </div>
  </div>
</template>
