<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
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
  if (s === 'completed' || s === 'passed') return 'bg-asi-purple-light text-asi-purple'
  if (s === 'incomplete') return 'bg-asi-orange-light text-asi-orange'
  if (s === 'failed') return 'bg-asi-red-light text-asi-red'
  return 'bg-asi-surface text-asi-gray'
})

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
    class="flex min-h-[100dvh] items-center justify-center text-sm text-asi-gray"
  >
    Loading course…
  </div>

  <!-- Page-level error -->
  <div
    v-else-if="pageError"
    class="flex min-h-[100dvh] flex-col items-center justify-center gap-4 px-4 text-center"
  >
    <p class="text-asi-gray">{{ pageError }}</p>
    <button
      type="button"
      class="rounded-lg bg-asi-purple px-5 py-2 text-sm font-medium text-white hover:bg-[#5a3a8a]"
      @click="goBack"
    >
      Back to courses
    </button>
  </div>

  <!-- Player layout -->
  <div v-else-if="course" class="flex flex-col h-[100dvh] bg-asi-surface">

    <!-- ── Top header ─────────────────────────────────────────────────────── -->
    <header class="flex items-center gap-3 px-4 py-3 bg-white border-b border-asi-border shrink-0">
      <button
        type="button"
        class="flex items-center gap-1.5 text-sm text-asi-gray hover:text-asi-black transition-colors shrink-0"
        @click="goBack"
      >
        <ArrowLeft :size="16" />
        Back
      </button>

      <div class="h-5 w-px bg-asi-border shrink-0" />

      <h1 class="text-sm font-semibold text-asi-black truncate flex-1">{{ courseTitle }}</h1>

      <span
        :class="clsx('text-xs font-semibold px-2.5 py-1 rounded-full shrink-0', statusColor)"
      >
        {{ statusLabel }}
      </span>
    </header>

    <!-- ── Progress bar ───────────────────────────────────────────────────── -->
    <div class="h-1.5 bg-asi-border shrink-0">
      <div
        class="h-full bg-gradient-to-r from-asi-purple to-asi-red transition-all duration-500"
        :style="{ width: `${progressPercent}%` }"
      />
    </div>

    <!-- ── Content area ───────────────────────────────────────────────────── -->
    <div class="flex-1 overflow-hidden">

      <!-- SCORM iframe — full width/height -->
      <iframe
        v-if="launchSrc"
        :title="courseTitle"
        class="w-full h-full border-0 bg-white"
        :src="launchSrc"
        allow="fullscreen; autoplay"
        sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-downloads allow-top-navigation-by-user-activation allow-popups-to-escape-sandbox"
      />

      <!-- No SCORM content -->
      <div
        v-else
        class="flex h-full flex-col items-center justify-center gap-3 text-sm text-asi-gray"
      >
        <p v-if="launchError" class="text-asi-orange text-center px-6">{{ launchError }}</p>
        <p v-else>No SCORM content available for this course.</p>
        <button
          type="button"
          class="rounded-lg bg-asi-purple px-5 py-2 text-sm font-medium text-white hover:bg-[#5a3a8a]"
          @click="goBack"
        >
          Back to courses
        </button>
      </div>
    </div>
  </div>
</template>
