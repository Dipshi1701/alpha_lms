<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Play, BookOpen, TrendingUp, X, Clock, Tag, Award, FileText, CheckCircle2, AlertCircle, BookMarked, ChevronDown } from 'lucide-vue-next'
import clsx from 'clsx'
import { fetchMyCoursesLearner, fetchMyProgress } from '../service'
import logo1 from '../../../assets/logo1.jpg'
import logo2 from '../../../assets/logo2.jpg'
import logo3 from '../../../assets/logo3.jpg'
import logo4 from '../../../assets/logo4.jpg'

const router = useRouter()

const activeFilter = ref('all')

const FILTERS = [
  { id: 'all',         label: 'All Courses',  icon: BookOpen      },
  { id: 'completed',   label: 'Completed',    icon: CheckCircle2  },
  { id: 'inprogress',  label: 'In Progress',  icon: TrendingUp    },
  { id: 'notstarted',  label: 'Not Started',  icon: BookMarked    },
  { id: 'due',         label: 'Due Course',   icon: Clock         },
  { id: 'overdue',     label: 'Overdue',      icon: AlertCircle   },
]

const courses = ref([])
const progressMap = ref({})
const loading = ref(true)
const loadError = ref('')
const search = ref('')

// ── Overview modal state ──────────────────────────────────────────────────────
const selectedCourse = ref(null)
const selectedCourseIdx = ref(0)

function openOverview(course, idx) {
  selectedCourse.value = course
  selectedCourseIdx.value = idx
  document.body.style.overflow = 'hidden'
}

function closeOverview() {
  selectedCourse.value = null
  document.body.style.overflow = ''
}

function launchCourse() {
  if (!selectedCourse.value) return
  const courseId = String(selectedCourse.value.id)
  closeOverview()
  router.push({ name: 'course-player', params: { courseId } })
}

// Close on Escape key
function onKeydown(e) {
  if (e.key === 'Escape') closeOverview()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [courseList, progress] = await Promise.all([
      fetchMyCoursesLearner(),
      fetchMyProgress().catch(() => ({})),
    ])
    courses.value = courseList
    progressMap.value = progress || {}
  } catch (e) {
    loadError.value = e?.message || 'Failed to load assignments'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function getCourseProgress(courseId) {
  return progressMap.value[String(courseId)] || { lesson_status: 'not attempted', progress_percent: 0 }
}

function statusLabel(status) {
  if (status === 'completed' || status === 'passed') return 'Completed'
  if (status === 'incomplete') return 'In Progress'
  if (status === 'failed') return 'Failed'
  return 'Not Started'
}

function actionLabel(status) {
  if (status === 'incomplete') return 'Resume Course'
  if (status === 'completed' || status === 'passed') return 'Review Course'
  return 'Start Course'
}

function statusBadgeClass(status) {
  if (status === 'completed' || status === 'passed') return 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/30'
  if (status === 'incomplete') return 'bg-amber-500/20 text-amber-200 border border-amber-400/30'
  if (status === 'failed') return 'bg-rose-500/20 text-rose-200 border border-rose-400/30'
  return 'bg-white/10 text-white/60 border border-white/20'
}

function statusBadgeClassLight(status) {
  if (status === 'completed' || status === 'passed') return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  if (status === 'incomplete') return 'bg-amber-50 text-amber-700 border border-amber-200'
  if (status === 'failed') return 'bg-rose-50 text-rose-700 border border-rose-200'
  return 'bg-[#F0EDF6] text-[#462C6B] border border-[#E8E2F0]'
}

function progressBarColor(status) {
  if (status === 'completed' || status === 'passed') return 'from-emerald-400 to-emerald-500'
  if (status === 'incomplete') return 'from-[#462C6B] to-[#CA1F47]'
  if (status === 'failed') return 'from-rose-400 to-rose-500'
  return 'from-[#462C6B] to-[#CA1F47]'
}

const CARD_LOGOS = [logo1, logo2, logo3, logo4]

function cardLogo(index) {
  return CARD_LOGOS[index % CARD_LOGOS.length]
}

function matchesFilter(course, filterId) {
  const p = getCourseProgress(course.id)
  const s = p.lesson_status
  if (filterId === 'all')        return true
  if (filterId === 'completed')  return s === 'completed' || s === 'passed'
  if (filterId === 'inprogress') return s === 'incomplete'
  if (filterId === 'notstarted') return s === 'not attempted' || s === 'unknown'
  if (filterId === 'due')        return s !== 'completed' && s !== 'passed' && s !== 'failed'
  if (filterId === 'overdue')    return s === 'failed'
  return true
}

const filterCounts = computed(() => {
  const counts = {}
  for (const f of FILTERS) {
    counts[f.id] = courses.value.filter(c => matchesFilter(c, f.id)).length
  }
  return counts
})

const filteredCourses = computed(() => {
  const q = search.value.toLowerCase().trim()
  let list = courses.value.filter(c => matchesFilter(c, activeFilter.value))
  if (q) list = list.filter(c => c.title?.toLowerCase().includes(q))
  return list
})
</script>

<template>
  <div class="min-h-screen bg-[#F7F5FA] p-6">

    <!-- ── Page header ──────────────────────────────────────────────────────── -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-asi-black">My Courses</h1>
        <p class="text-sm text-asi-gray mt-0.5">Track and continue your assigned learning</p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <!-- Search -->
        <div class="relative w-full sm:w-56">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
          <input
            v-model="search"
            placeholder="Search courses…"
            class="w-full h-10 pl-9 pr-4 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] shadow-sm placeholder:text-[#7D6B9D]/60"
          />
        </div>

        <!-- Filter dropdown -->
        <div class="relative">
          <select
            v-model="activeFilter"
            class="appearance-none h-10 pl-4 pr-9 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] cursor-pointer shadow-sm"
          >
            <option v-for="f in FILTERS" :key="f.id" :value="f.id">
              {{ f.label }} ({{ filterCounts[f.id] }})
            </option>
          </select>
          <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="loadError" class="mb-5 rounded-xl border border-[#FAEAEE] bg-[#FAEAEE] text-[#CA1F47] px-4 py-3 text-sm">
      {{ loadError }}
    </div>

    <!-- ── Course grid ──────────────────────────────────────────────────────── -->

    <!-- Loading skeletons -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div v-for="i in 8" :key="i" class="rounded-2xl overflow-hidden bg-white shadow-sm border border-[#E8E2F0]">
        <div class="h-40 bg-gradient-to-br from-[#E8E2F0] to-[#F0EDF6] animate-pulse" />
        <div class="p-4 space-y-3">
          <div class="h-3.5 rounded-full bg-[#F0EDF6] animate-pulse w-3/4" />
          <div class="h-3 rounded-full bg-[#F0EDF6] animate-pulse w-1/2" />
          <div class="h-1.5 rounded-full bg-[#F0EDF6] animate-pulse mt-2" />
          <div class="h-8 rounded-xl bg-[#F0EDF6] animate-pulse mt-3" />
        </div>
      </div>
    </div>

    <!-- Course cards -->
    <div v-else-if="filteredCourses.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="(course, idx) in filteredCourses"
        :key="course.id"
        class="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:shadow-[#462C6B]/15 border border-[#E8E2F0] hover:border-[#7D6B9D]/30 cursor-pointer transition-all duration-300 hover:-translate-y-1 flex flex-col"
        @click="openOverview(course, idx)"
      >
        <!-- Thumbnail -->
        <div class="relative h-40 overflow-hidden bg-[#231F20]">
          <img :src="cardLogo(idx)" :alt="course.title" class="w-full h-full object-cover opacity-90" />
          <div class="absolute top-3 left-3 right-3 flex items-center justify-between">
            <span class="text-[10px] font-bold px-2.5 py-1 rounded-full bg-black/40 text-white/90 backdrop-blur-sm uppercase tracking-wide">
              SCORM 1.2
            </span>
            <span :class="clsx('text-[10px] font-bold px-2.5 py-1 rounded-full backdrop-blur-sm', statusBadgeClass(getCourseProgress(course.id).lesson_status))">
              {{ statusLabel(getCourseProgress(course.id).lesson_status) }}
            </span>
          </div>
        </div>

        <!-- Card body -->
        <div class="p-4 flex flex-col flex-1">
          <h3 class="font-bold text-[#231F20] text-sm leading-snug line-clamp-2 mb-2 group-hover:text-[#462C6B] transition-colors">
            {{ course.title }}
          </h3>
          <div class="flex items-center gap-2 mb-4">
            <span class="inline-flex items-center text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#F0EDF6] text-[#462C6B]">
              {{ course.category || 'General' }}
            </span>
          </div>

          <div class="mt-auto mb-4">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[11px] font-medium text-[#67686B]">Progress</span>
              <span class="text-[11px] font-extrabold text-[#462C6B]">
                {{ getCourseProgress(course.id).progress_percent }}%
              </span>
            </div>
            <div class="h-2 rounded-full bg-[#F0EDF6] overflow-hidden">
              <div
                class="h-full rounded-full bg-gradient-to-r from-[#462C6B] to-[#CA1F47] transition-all duration-700"
                :style="{ width: `${getCourseProgress(course.id).progress_percent}%` }"
              />
            </div>
          </div>

          <button
            type="button"
            class="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#462C6B] to-[#462C6B] hover:from-[#462C6B] hover:to-[#CA1F47] hover:shadow-md hover:shadow-[#462C6B]/30 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 shadow-sm"
            @click.stop="openOverview(course, idx)"
          >
            <BookOpen :size="11" />
            View Course
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-dashed border-[#E8E2F0]">
      <div class="w-16 h-16 rounded-2xl bg-[#F0EDF6] flex items-center justify-center mb-4">
        <BookOpen :size="24" class="text-[#7D6B9D]" />
      </div>
      <h3 class="text-base font-bold text-[#231F20] mb-1">No courses found</h3>
      <p class="text-sm text-[#67686B] text-center max-w-xs">
        {{ activeFilter === 'all' ? 'No courses have been assigned to you yet.' : 'No courses match this filter.' }}
      </p>
      <button
        v-if="activeFilter !== 'all'"
        type="button"
        class="mt-4 text-xs font-bold text-[#462C6B] hover:text-[#CA1F47] transition-colors"
        @click="activeFilter = 'all'"
      >
        Show all courses
      </button>
    </div>

    <!-- ── Course Overview Modal ────────────────────────────────────────────── -->
    <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="selectedCourse"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="closeOverview"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="closeOverview" />

        <!-- Modal panel -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 scale-95 translate-y-4"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-4"
          appear
        >
          <div
            v-if="selectedCourse"
            class="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden z-10 max-h-[90vh] flex flex-col"
          >
            <!-- Close button -->
            <button
              type="button"
              class="absolute top-4 right-4 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/50 text-white backdrop-blur-sm transition-colors"
              @click="closeOverview"
            >
              <X :size="16" />
            </button>

            <!-- Hero image -->
            <div class="relative h-52 flex-shrink-0 overflow-hidden bg-[#231F20]">
              <img
                :src="cardLogo(selectedCourseIdx)"
                :alt="selectedCourse.title"
                class="w-full h-full object-cover opacity-85"
              />
              <!-- Gradient fade at bottom for text readability -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

              <!-- Status badge on image -->
              <div class="absolute bottom-4 left-5 right-14 flex items-end justify-between">
                <span :class="clsx('text-[11px] font-bold px-3 py-1 rounded-full backdrop-blur-sm', statusBadgeClass(getCourseProgress(selectedCourse.id).lesson_status))">
                  {{ statusLabel(getCourseProgress(selectedCourse.id).lesson_status) }}
                </span>
                <span class="text-[11px] font-bold px-3 py-1 rounded-full bg-black/40 text-white/90 backdrop-blur-sm uppercase tracking-wide">
                  SCORM 1.2
                </span>
              </div>
            </div>

            <!-- Scrollable body -->
            <div class="flex-1 overflow-y-auto">
              <div class="p-6">

                <!-- Title -->
                <h2 class="text-lg font-extrabold text-[#231F20] leading-snug mb-3">
                  {{ selectedCourse.title }}
                </h2>

                <!-- Meta chips row -->
                <div class="flex flex-wrap items-center gap-2 mb-5">
                  <span class="inline-flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1 rounded-full bg-[#F0EDF6] text-[#462C6B]">
                    <Tag :size="11" />
                    {{ selectedCourse.category || 'General' }}
                  </span>
                  <span class="inline-flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1 rounded-full bg-[#F0EDF6] text-[#462C6B]">
                    <FileText :size="11" />
                    {{ selectedCourse.content_type || 'SCORM 1.2' }}
                  </span>
                  <span v-if="selectedCourse.scorm_maxtimeallowed" class="inline-flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1 rounded-full bg-[#F0EDF6] text-[#462C6B]">
                    <Clock :size="11" />
                    {{ selectedCourse.scorm_maxtimeallowed }}
                  </span>
                </div>

                <!-- Divider -->
                <div class="h-px bg-[#F0EDF6] mb-5" />

                <!-- Progress section -->
                <div class="mb-5">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-semibold text-[#231F20]">Your Progress</span>
                    <span class="text-sm font-extrabold text-[#462C6B]">
                      {{ getCourseProgress(selectedCourse.id).progress_percent }}%
                    </span>
                  </div>
                  <div class="h-2.5 rounded-full bg-[#F0EDF6] overflow-hidden">
                    <div
                      :class="clsx('h-full rounded-full bg-gradient-to-r transition-all duration-700', progressBarColor(getCourseProgress(selectedCourse.id).lesson_status))"
                      :style="{ width: `${getCourseProgress(selectedCourse.id).progress_percent}%` }"
                    />
                  </div>
                </div>

                <!-- Divider -->
                <div class="h-px bg-[#F0EDF6] mb-5" />

                <!-- Description -->
                <div class="mb-6">
                  <div class="flex items-center gap-2 mb-2">
                    <Award :size="14" class="text-[#462C6B]" />
                    <span class="text-sm font-semibold text-[#231F20]">About this Course</span>
                  </div>
                  <p v-if="selectedCourse.description" class="text-sm text-[#67686B] leading-relaxed">
                    {{ selectedCourse.description }}
                  </p>
                  <p v-else class="text-sm text-[#67686B]/60 italic">
                    No description available for this course.
                  </p>
                </div>

              </div>
            </div>

            <!-- Sticky footer CTA -->
            <div class="flex-shrink-0 px-6 py-4 border-t border-[#F0EDF6] bg-white">
              <button
                type="button"
                class="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl text-sm font-bold text-white bg-gradient-to-r from-[#462C6B] to-[#CA1F47] hover:from-[#CA1F47] hover:to-[#462C6B] hover:shadow-xl hover:shadow-[#462C6B]/40 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
                @click="launchCourse"
              >
                <Play :size="15" class="fill-current" />
                {{ actionLabel(getCourseProgress(selectedCourse.id).lesson_status) }}
              </button>
            </div>

          </div>
        </Transition>
      </div>
    </Transition>
    </Teleport>
  </div>
</template>
