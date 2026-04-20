<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Play, CheckCircle2, Clock, BookOpen } from 'lucide-vue-next'
import clsx from 'clsx'
import { fetchMyCoursesLearner, fetchMyProgress } from '../service'

const router = useRouter()

// ── Tabs ─────────────────────────────────────────────────────────────────────

const activeTab = ref('assignments') // 'assignments' | 'learning'

// ── Data ─────────────────────────────────────────────────────────────────────

const courses = ref([])
const progressMap = ref({}) // { [courseId]: { lesson_status, progress_percent } }
const loading = ref(true)
const loadError = ref('')
const search = ref('')

// ── Load ──────────────────────────────────────────────────────────────────────

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

// ── Helpers ───────────────────────────────────────────────────────────────────

function getCourseProgress(courseId) {
  return progressMap.value[String(courseId)] || { lesson_status: 'not attempted', progress_percent: 0 }
}

function statusLabel(status) {
  if (status === 'completed' || status === 'passed') return 'Completed'
  if (status === 'incomplete') return 'In Progress'
  if (status === 'failed') return 'Failed'
  return 'Not Started'
}

function statusColorClass(status) {
  if (status === 'completed' || status === 'passed') return 'bg-green-100 text-green-700'
  if (status === 'incomplete') return 'bg-amber-100 text-amber-700'
  if (status === 'failed') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-500'
}

// ── Filtered lists ────────────────────────────────────────────────────────────

const filteredAssignments = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return courses.value
  return courses.value.filter((c) => c.title?.toLowerCase().includes(q))
})

// My Learning = courses where the learner has actually started (progress > 0)
const myLearning = computed(() =>
  courses.value.filter((c) => {
    const p = getCourseProgress(c.id)
    return p.lesson_status !== 'not attempted' && p.progress_percent > 0
  })
)

const filteredLearning = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return myLearning.value
  return myLearning.value.filter((c) => c.title?.toLowerCase().includes(q))
})

// ── Navigation ────────────────────────────────────────────────────────────────

function openCourse(courseId) {
  router.push({ name: 'course-player', params: { courseId: String(courseId) } })
}
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">

    <!-- Page title -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-800">My Courses</h1>
      <p class="text-sm text-gray-500 mt-0.5">Your assigned training and learning activity</p>
    </div>

    <!-- Error banner -->
    <div
      v-if="loadError"
      class="mb-5 rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm"
    >
      {{ loadError }}
    </div>

    <!-- Pill tabs -->
    <div class="flex flex-wrap items-center gap-2 mb-6 border-b border-gray-200 pb-4">
      <button
        type="button"
        @click="activeTab = 'assignments'"
        :class="clsx(
          'px-4 py-2 rounded-full text-sm font-semibold transition-colors',
          activeTab === 'assignments'
            ? 'bg-[#2d1b69] text-white'
            : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
        )"
      >
        My Assignments
        <span
          v-if="courses.length"
          :class="clsx(
            'ml-1.5 text-xs px-1.5 py-0.5 rounded-full',
            activeTab === 'assignments' ? 'bg-white/20' : 'bg-gray-200 text-gray-600'
          )"
        >{{ courses.length }}</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'learning'"
        :class="clsx(
          'px-4 py-2 rounded-full text-sm font-semibold transition-colors',
          activeTab === 'learning'
            ? 'bg-[#2d1b69] text-white'
            : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
        )"
      >
        My Learning
        <span
          v-if="myLearning.length"
          :class="clsx(
            'ml-1.5 text-xs px-1.5 py-0.5 rounded-full',
            activeTab === 'learning' ? 'bg-white/20' : 'bg-gray-200 text-gray-600'
          )"
        >{{ myLearning.length }}</span>
      </button>
    </div>

    <!-- Search -->
    <div class="relative max-w-sm mb-5">
      <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
      <input
        v-model="search"
        placeholder="Search courses…"
        class="w-full pl-9 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400"
      />
    </div>

    <!-- ── My Assignments tab ────────────────────────────────────────────── -->
    <div v-show="activeTab === 'assignments'">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 4" :key="i" class="h-16 rounded-xl bg-gray-100 animate-pulse" />
      </div>

      <div v-else class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Course</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Category</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Progress</th>
                <th class="text-right px-4 py-3 font-semibold text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="course in filteredAssignments"
                :key="course.id"
                class="border-b border-gray-100 hover:bg-purple-50/40 cursor-pointer transition-colors"
                @click="openCourse(course.id)"
              >
                <!-- Course title + icon -->
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div
                      :class="clsx(
                        'w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold shrink-0',
                        course.color || 'bg-slate-400'
                      )"
                    >
                      {{ course.title?.[0] || 'C' }}
                    </div>
                    <div class="min-w-0">
                      <p class="font-semibold text-gray-900 truncate">{{ course.title }}</p>
                      <span class="text-xs text-purple-600 font-medium">SCORM 1.2</span>
                    </div>
                  </div>
                </td>

                <!-- Category -->
                <td class="px-4 py-3 text-gray-600">{{ course.category || '—' }}</td>

                <!-- Progress -->
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <!-- Progress bar -->
                    <div class="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        class="h-full bg-[#2d1b69] rounded-full transition-all duration-300"
                        :style="{ width: `${getCourseProgress(course.id).progress_percent}%` }"
                      />
                    </div>
                    <!-- Status badge -->
                    <span
                      :class="clsx(
                        'text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap',
                        statusColorClass(getCourseProgress(course.id).lesson_status)
                      )"
                    >
                      {{ statusLabel(getCourseProgress(course.id).lesson_status) }}
                    </span>
                  </div>
                </td>

                <!-- Action button -->
                <td class="px-4 py-3 text-right">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#2d1b69] text-white hover:bg-[#231450] transition-colors"
                    @click.stop="openCourse(course.id)"
                  >
                    <Play :size="12" />
                    {{
                      getCourseProgress(course.id).lesson_status === 'incomplete'
                        ? 'Resume'
                        : getCourseProgress(course.id).lesson_status === 'completed' || getCourseProgress(course.id).lesson_status === 'passed'
                          ? 'Review'
                          : 'Start'
                    }}
                  </button>
                </td>
              </tr>

              <!-- Empty state -->
              <tr v-if="filteredAssignments.length === 0">
                <td colspan="4" class="px-4 py-12 text-center text-sm text-gray-500">
                  No assignments yet. When an instructor assigns you a published course, it will appear here.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ── My Learning tab ───────────────────────────────────────────────── -->
    <div v-show="activeTab === 'learning'">
      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 2" :key="i" class="h-16 rounded-xl bg-gray-100 animate-pulse" />
      </div>

      <!-- Has in-progress / completed courses -->
      <div
        v-else-if="filteredLearning.length > 0"
        class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden"
      >
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Course</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Category</th>
                <th class="text-left px-4 py-3 font-semibold text-gray-700">Progress</th>
                <th class="text-right px-4 py-3 font-semibold text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="course in filteredLearning"
                :key="course.id"
                class="border-b border-gray-100 hover:bg-purple-50/40 cursor-pointer transition-colors"
                @click="openCourse(course.id)"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div
                      :class="clsx(
                        'w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold shrink-0',
                        course.color || 'bg-slate-400'
                      )"
                    >
                      {{ course.title?.[0] || 'C' }}
                    </div>
                    <div class="min-w-0">
                      <p class="font-semibold text-gray-900 truncate">{{ course.title }}</p>
                      <span class="text-xs text-purple-600 font-medium">SCORM 1.2</span>
                    </div>
                  </div>
                </td>

                <td class="px-4 py-3 text-gray-600">{{ course.category || '—' }}</td>

                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <div class="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        class="h-full bg-[#2d1b69] rounded-full transition-all duration-300"
                        :style="{ width: `${getCourseProgress(course.id).progress_percent}%` }"
                      />
                    </div>
                    <span
                      :class="clsx(
                        'text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap',
                        statusColorClass(getCourseProgress(course.id).lesson_status)
                      )"
                    >
                      {{ statusLabel(getCourseProgress(course.id).lesson_status) }}
                    </span>
                  </div>
                </td>

                <td class="px-4 py-3 text-right">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#2d1b69] text-white hover:bg-[#231450] transition-colors"
                    @click.stop="openCourse(course.id)"
                  >
                    <Play :size="12" />
                    {{
                      getCourseProgress(course.id).lesson_status === 'incomplete'
                        ? 'Resume'
                        : 'Review'
                    }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Empty state (nothing started yet) -->
      <div
        v-else
        class="rounded-2xl border border-dashed border-gray-200 bg-gray-50/80 px-6 py-16 text-center"
      >
        <BookOpen :size="28" class="mx-auto text-gray-300 mb-3" />
        <p class="text-sm font-medium text-gray-700">Nothing here yet</p>
        <p class="text-sm text-gray-500 mt-2 max-w-sm mx-auto">
          Courses you start or complete will appear here so you can track your learning progress.
        </p>
        <button
          type="button"
          class="mt-4 text-sm font-semibold text-[#2d1b69] hover:underline"
          @click="activeTab = 'assignments'"
        >
          Go to My Assignments →
        </button>
      </div>
    </div>

  </div>
</template>
