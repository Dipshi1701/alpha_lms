<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, BookOpen, CheckCircle2, PlayCircle } from 'lucide-vue-next'
import clsx from 'clsx'
import { apiUrl } from '../../../api/httpClient'
import {
  fetchCourse,
  fetchLaunchUrl,
  fetchScormState,
} from '../service'
import { installFullScormApi, removeFullScormApi } from '../scorm/scorm12FullApi'

const route = useRoute()
const router = useRouter()

// ── Route param ──────────────────────────────────────────────────────────────

const courseId = computed(() => {
  const n = Number(route.params.courseId)
  return Number.isFinite(n) ? n : null
})

// ── Component state ──────────────────────────────────────────────────────────

const course         = ref(null)
const loading        = ref(true)
const pageError      = ref('')
const launchError    = ref('')
const launchPath     = ref('')
const progressPercent = ref(0)
const lessonStatus   = ref('not attempted')

// ── Computed ─────────────────────────────────────────────────────────────────

const launchSrc   = computed(() => (launchPath.value ? apiUrl(launchPath.value) : ''))
const courseTitle = computed(() => course.value?.title || 'Course')

const statusLabel = computed(() => {
  const s = lessonStatus.value
  if (s === 'completed' || s === 'passed') return 'Completed'
  if (s === 'incomplete') return 'In Progress'
  if (s === 'failed') return 'Failed'
  return 'Not Started'
})

const statusColor = computed(() => {
  const s = lessonStatus.value
  if (s === 'completed' || s === 'passed') return 'bg-green-100 text-green-700'
  if (s === 'incomplete') return 'bg-amber-100 text-amber-700'
  if (s === 'failed') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-600'
})

// SVG progress ring
const RADIUS = 20
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const strokeDashoffset = computed(() => CIRCUMFERENCE * (1 - progressPercent.value / 100))

// ── scormPost ────────────────────────────────────────────────────────────────
// window.scormPost is called by scorm12FullApi.js on every LMSCommit / LMSFinish.
// We install it here so it has access to courseId and the auth token.
// It decides commit vs finish based on whether session_time is present in the payload
// (the JS runtime only sends session_time on LMSFinish).

function installScormPost(id) {
  window.scormPost = async function scormPost(data) {
    const isFinish = data.session_time !== undefined && data.session_time !== ''
    const url = isFinish
      ? `/api/scorm/${id}/finish`
      : `/api/scorm/${id}/commit`

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        console.warn('[SCORM] scormPost HTTP error:', response.status)
        return
      }

      const json = await response.json()
      const result = json?.data

      // Keep the UI in sync with whatever the backend saved
      if (result?.lesson_status) {
        lessonStatus.value = result.lesson_status
      }
      if (result?.progress_percent !== undefined) {
        progressPercent.value = result.progress_percent
      }
    } catch (e) {
      console.warn('[SCORM] scormPost failed:', e?.message)
    }
  }
}

function removeScormPost() {
  window.scormPost = undefined
}

// ── Load player ──────────────────────────────────────────────────────────────

async function loadPlayer() {
  // Clean up any previously installed API and globals
  removeFullScormApi()
  removeScormPost()

  loading.value         = true
  pageError.value       = ''
  launchError.value     = ''
  launchPath.value      = ''
  course.value          = null
  progressPercent.value = 0
  lessonStatus.value    = 'not attempted'

  const id = courseId.value
  if (!id) {
    pageError.value = 'Invalid course link.'
    loading.value   = false
    return
  }

  try {
    // Fetch course details and raw SCORM launch state in parallel
    const [courseData, launchState] = await Promise.all([
      fetchCourse(id),
      fetchScormState(id).catch(() => null),
    ])

    console.log('courseData', launchState)
    course.value = courseData

    // Update the UI status badge from saved state
    if (launchState) {
      lessonStatus.value = launchState.lesson_status || 'not attempted'
      if (launchState.lesson_status === 'completed' || launchState.lesson_status === 'passed') {
        progressPercent.value = 100
      } else if (launchState.lesson_status === 'incomplete') {
        progressPercent.value = 50
      }
    }

    try {
      const res = await fetchLaunchUrl(id)
      const url = res?.launch_url || ''

      if (url) {
        // ── Step 1: Set window.tl_sco_data ────────────────────────────────
        // scorm12FullApi.js reads this at LMSInitialize() time to fill the CMI tree.
        // Must be set BEFORE the iframe loads.
        window.tl_sco_data = {
          student_id:        launchState?.student_id        || String(id),
          student_name:      launchState?.student_name      || 'Learner',
          lesson_location:   launchState?.lesson_location   || '',
          suspend_data:      launchState?.suspend_data      || '',
          lesson_status:     launchState?.lesson_status     || 'not attempted',
          score_raw:         launchState?.score_raw         || '',
          total_time:        launchState?.total_time        || '0000:00:00.00',
          entry:             launchState?.entry             || 'ab-initio',
          datafromlms:       launchState?.datafromlms       || '',
          masteryscore:      launchState?.masteryscore      || '',
          maxtimeallowed:    launchState?.maxtimeallowed    || '',
          timelimitaction:   launchState?.timelimitaction   || '',
          lesson_mode:       launchState?.lesson_mode       || 'normal',
          comments_from_lms: launchState?.comments_from_lms || '',
        }

        // ── Step 2: Set window.scormPost ──────────────────────────────────
        // scorm12FullApi.js calls window.scormPost(data) on every LMSCommit / LMSFinish.
        installScormPost(id)

        // ── Step 3: Install window.API from scorm12FullApi.js ─────────────
        // This sets window.API (and window.top.API) so the SCORM course
        // inside the iframe can find the LMS runtime on the parent frame.
        installFullScormApi()
      }

      launchPath.value = url
    } catch (e) {
      launchError.value = e?.message || 'Unable to load SCORM content.'
    }
  } catch (e) {
    pageError.value = e?.message || 'Course not found or not available.'
  } finally {
    loading.value = false
  }
}

onMounted(loadPlayer)
watch(() => route.params.courseId, loadPlayer)
onBeforeUnmount(() => {
  removeFullScormApi()
  removeScormPost()
  window.tl_sco_data = undefined
})

function goBack() {
  router.push('/courses')
}
</script>

<template>
  <!-- Loading -->
  <div
    v-if="loading"
    class="flex min-h-[100dvh] items-center justify-center text-sm text-gray-500"
  >
    Loading course…
  </div>

  <!-- Page-level error -->
  <div
    v-else-if="pageError"
    class="flex min-h-[100dvh] flex-col items-center justify-center gap-4 px-4 text-center"
  >
    <p class="text-gray-700">{{ pageError }}</p>
    <button
      type="button"
      class="rounded-lg bg-[#2d1b69] px-5 py-2 text-sm font-medium text-white hover:bg-[#231450]"
      @click="goBack"
    >
      Back to courses
    </button>
  </div>

  <!-- Player layout -->
  <div v-else-if="course" class="flex flex-col h-[100dvh] bg-gray-100">

    <!-- ── Top header ─────────────────────────────────────────────────────── -->
    <header class="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 shrink-0">
      <button
        type="button"
        class="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors shrink-0"
        @click="goBack"
      >
        <ArrowLeft :size="16" />
        Back
      </button>

      <div class="h-5 w-px bg-gray-200 shrink-0" />

      <h1 class="text-sm font-semibold text-gray-900 truncate flex-1">{{ courseTitle }}</h1>

      <span
        :class="clsx('text-xs font-semibold px-2.5 py-1 rounded-full shrink-0', statusColor)"
      >
        {{ statusLabel }}
      </span>
    </header>

    <!-- ── Progress bar ───────────────────────────────────────────────────── -->
    <div class="h-1.5 bg-gray-200 shrink-0">
      <div
        class="h-full bg-[#2d1b69] transition-all duration-500"
        :style="{ width: `${progressPercent}%` }"
      />
    </div>

    <!-- ── Content area ───────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- SCORM iframe (left, main) -->
      <div v-if="launchSrc" class="flex-1 overflow-hidden min-w-0">
        <iframe
          :title="courseTitle"
          class="w-full h-full border-0 bg-white"
          :src="launchSrc"
          allow="fullscreen; autoplay"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-downloads allow-top-navigation-by-user-activation allow-popups-to-escape-sandbox"
        />
      </div>

      <!-- No SCORM content -->
      <div
        v-else
        class="flex-1 flex flex-col items-center justify-center gap-3 text-sm text-gray-500"
      >
        <p v-if="launchError" class="text-amber-600 text-center px-6">{{ launchError }}</p>
        <p v-else>No SCORM content available for this course.</p>
        <button
          type="button"
          class="rounded-lg bg-[#2d1b69] px-5 py-2 text-sm font-medium text-white hover:bg-[#231450]"
          @click="goBack"
        >
          Back to courses
        </button>
      </div>

      <!-- ── Right aside ─────────────────────────────────────────────────── -->
      <aside class="w-72 shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-y-auto">

        <!-- Progress ring -->
        <div class="px-5 py-4 border-b border-gray-100">
          <div class="flex items-center gap-3">
            <div class="relative w-12 h-12 shrink-0">
              <svg class="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="20" stroke="#e5e7eb" stroke-width="4" fill="none" />
                <circle
                  cx="24" cy="24" r="20"
                  stroke="#2d1b69"
                  stroke-width="4"
                  fill="none"
                  :stroke-dasharray="CIRCUMFERENCE"
                  :stroke-dashoffset="strokeDashoffset"
                  stroke-linecap="round"
                  class="transition-all duration-500"
                />
              </svg>
              <span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-[#2d1b69]">
                {{ progressPercent }}%
              </span>
            </div>
            <div>
              <p class="text-sm font-semibold text-gray-900">{{ statusLabel }}</p>
              <p class="text-xs text-gray-500 mt-0.5">Overall progress</p>
            </div>
          </div>
        </div>

        <!-- Course info -->
        <div class="px-5 py-4 border-b border-gray-100">
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">About</p>
          <p v-if="course.description" class="text-sm text-gray-700 leading-relaxed">
            {{ course.description }}
          </p>
          <p v-else class="text-sm text-gray-400 italic">No description provided.</p>

          <div class="flex flex-wrap gap-1.5 mt-3">
            <span
              v-if="course.category"
              class="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-100 font-medium"
            >
              {{ course.category }}
            </span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100 font-medium">
              SCORM 1.2
            </span>
          </div>
        </div>

        <!-- Lesson list -->
        <div class="px-5 py-4 flex-1">
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Lessons</p>

          <div class="space-y-2">
            <div class="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100">
              <!-- Status icon -->
              <div class="mt-0.5 shrink-0">
                <CheckCircle2
                  v-if="lessonStatus === 'completed' || lessonStatus === 'passed'"
                  :size="16"
                  class="text-green-500"
                />
                <PlayCircle
                  v-else-if="lessonStatus === 'incomplete' && progressPercent > 0"
                  :size="16"
                  class="text-amber-500"
                />
                <BookOpen v-else :size="16" class="text-gray-400" />
              </div>

              <div class="min-w-0">
                <p class="text-sm font-medium text-gray-800 truncate">
                  {{ course.scormManifestTitle || course.title }}
                </p>
                <p class="text-xs text-gray-500 mt-0.5">{{ statusLabel }}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
