<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  BookPlus,
  Search,
  Pencil,
  Trash2,
  Users as UsersIcon,
  Eye,
  ChevronDown,
} from 'lucide-vue-next'
import clsx from 'clsx'
import CourseUpsertModal from '../modals/CourseUpsertModal.vue'
import CourseAssignModal from '../modals/CourseAssignModal.vue'
import {
  fetchCoursesAdmin,
  fetchAssignableUsers,
  createCourse,
  updateCourse,
  deleteCourse,
  assignCourseUsers,
  uploadScormZip,
} from '../service'
// Group course assignment (G011) reuses the exact Groups API/service built
// in G010 — no second assignment architecture. Assigning a course to a
// group is Administrator-only on the backend (see G006/G009), so this is
// only ever loaded/offered when isAdmin is true.
import { fetchGroups, assignGroupCourse } from '../../users/service'
import { useAccess } from '../../../composables/useAccess'

const CATEGORIES = ['All', 'General', 'Sales', 'Management', 'Compliance', 'Technical']

const router = useRouter()
const { isAdmin } = useAccess()

const courses = ref([])
const assignableUsers = ref([])
const loading = ref(true)
const loadError = ref('')
const openLearnerPreview = (course) => {
  router.push({
    name: 'course-player',
    params: { courseId: String(course.id) },
    query: { preview: '1' },
  })
}

const search = ref('')
const category = ref('All')
const showAddCourseModal = ref(false)
const snackbarMessage = ref('')
const snackbarTone = ref('success') // success | error
const showSnackbar = ref(false)
let snackbarTimer = null
const isEditMode = ref(false)
const editingCourseId = ref(null)
const isSubmittingCourse = ref(false)
const showAssignModal = ref(false)
const assigningCourse = ref(null)
const isSubmittingAssignment = ref(false)
const groupsForAssignment = ref([])
const groupsForAssignmentLoading = ref(false)
const groupsForAssignmentError = ref('')

const addCourseForm = reactive({
  title: '',
  category: 'General',
  description: '',
  status: 'Draft',
  assignmentDurationDays: 7,
})

const assignForm = reactive({
  assignedUserIds: [],
})

const filtered = computed(() =>
  courses.value.filter((c) => {
    const matchSearch = c.title.toLowerCase().includes(search.value.toLowerCase())
    const matchCat = category.value === 'All' || c.category === category.value
    return matchSearch && matchCat
  })
)

const resetAddCourseForm = () => {
  addCourseForm.title = ''
  addCourseForm.category = 'General'
  addCourseForm.description = ''
  addCourseForm.status = 'Draft'
  addCourseForm.assignmentDurationDays = 7
  editingCourseId.value = null
  isEditMode.value = false
}

const openAddCourseModal = () => {
  showSnackbar.value = false
  resetAddCourseForm()
  showAddCourseModal.value = true
}

const openEditCourseModal = (course) => {
  showSnackbar.value = false
  isEditMode.value = true
  editingCourseId.value = course.id
  addCourseForm.title = course.title || ''
  addCourseForm.category = course.category || 'General'
  addCourseForm.description = course.description || ''
  addCourseForm.status = course.status || 'Draft'
  addCourseForm.assignmentDurationDays = course.assignmentDurationDays ?? 7
  showAddCourseModal.value = true
}

const closeAddCourseModal = () => {
  if (isSubmittingCourse.value) return
  showAddCourseModal.value = false
}

const canAssignCourse = (course) => course?.status === 'Published'

const notify = (message, tone = 'success') => {
  if (!message) return
  snackbarMessage.value = message
  snackbarTone.value = tone
  showSnackbar.value = true
  if (snackbarTimer) clearTimeout(snackbarTimer)
  snackbarTimer = setTimeout(() => {
    showSnackbar.value = false
  }, 3200)
}

const loadGroupsForAssignment = async () => {
  if (!isAdmin.value) return
  groupsForAssignmentLoading.value = true
  groupsForAssignmentError.value = ''
  try {
    // Backend is the source of truth for scope — render exactly what
    // GET /api/groups returns, no client-side filtering.
    groupsForAssignment.value = await fetchGroups()
  } catch (e) {
    groupsForAssignmentError.value = e?.message || 'Failed to load groups'
  } finally {
    groupsForAssignmentLoading.value = false
  }
}

const openAssignModal = (course) => {
  if (!canAssignCourse(course)) return
  assigningCourse.value = course
  assignForm.assignedUserIds = [...(course.assignedUserIds || [])]
  showAssignModal.value = true
  if (isAdmin.value) loadGroupsForAssignment()
}

const closeAssignModal = () => {
  if (isSubmittingAssignment.value) return
  showAssignModal.value = false
  assigningCourse.value = null
}

const loadData = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const [cRows, uRows] = await Promise.all([
      fetchCoursesAdmin(),
      fetchAssignableUsers(),
    ])
    courses.value = cRows
    assignableUsers.value = uRows
  } catch (e) {
    loadError.value = e?.message || 'Failed to load courses'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
onBeforeUnmount(() => {
  if (snackbarTimer) clearTimeout(snackbarTimer)
})

const saveAssignment = async () => {
  if (!assigningCourse.value || isSubmittingAssignment.value) return
  isSubmittingAssignment.value = true
  try {
    // Replaces the full assignment list for this course — assignForm
    // already starts from the course's current (source-agnostic)
    // assigned_user_ids, so learners assigned via a Group are preserved
    // unless explicitly un-toggled here.
    await assignCourseUsers(assigningCourse.value.id, assignForm.assignedUserIds)
    const names = assignableUsers.value
      .filter((u) => assignForm.assignedUserIds.includes(u.id))
      .map((u) => u.name)
    notify(
      names.length
        ? `Assigned "${assigningCourse.value.title}" → ${names.join(', ')}`
        : `Cleared assignments for "${assigningCourse.value.title}"`,
      'success'
    )
    closeAssignModal()
    await loadData()
  } catch (e) {
    notify(e?.message || 'Assignment failed', 'error')
  } finally {
    isSubmittingAssignment.value = false
  }
}

const saveGroupAssignment = async (groupId) => {
  if (!assigningCourse.value || isSubmittingAssignment.value) return
  isSubmittingAssignment.value = true
  try {
    // Existing GroupCourseAssignment + G007 learner-sync flow — no second
    // assignment system. The backend's own duplicate-assignment rule
    // (course already assigned to this group) surfaces here unchanged.
    await assignGroupCourse(groupId, assigningCourse.value.id)
    const group = groupsForAssignment.value.find((g) => g.id === groupId)
    notify(
      `Assigned "${assigningCourse.value.title}" to group "${group?.name || groupId}"`,
      'success'
    )
    closeAssignModal()
    await loadData()
  } catch (e) {
    notify(e?.message || 'Group assignment failed', 'error')
  } finally {
    isSubmittingAssignment.value = false
  }
}

const submitCourse = async (payload) => {
  if (isSubmittingCourse.value) return
  isSubmittingCourse.value = true
  const isCreate = !isEditMode.value
  const scormFile = payload?.scormFile
  // G012: falls back to the same backward-compatible default (7) as the
  // backend if the modal somehow didn't provide one — the modal's own
  // validation already blocks submitting anything invalid before this
  // handler ever runs.
  const assignmentDurationDays = Number(payload?.assignmentDurationDays) || 7
  const base = {
    title: payload?.title?.trim() || 'Untitled course',
    category: payload?.category || 'General',
    description: (payload?.description || '').trim() || null,
    status: payload?.status || 'Draft',
    code: '-',
    price: '-',
    assignment_duration_days: assignmentDurationDays,
  }

  try {
    let courseId
    if (isEditMode.value && editingCourseId.value != null) {
      courseId = editingCourseId.value
      await updateCourse(courseId, { ...base })
      notify(`Updated "${base.title}"`, 'success')
    } else {
      const created = await createCourse({
        ...base,
        status: 'Draft',
      })
      courseId = created.id
      notify(`Created "${base.title}"`, 'success')
    }

    if (scormFile && scormFile instanceof File) {
      await uploadScormZip(courseId, scormFile)
      notify(`SCORM uploaded and validated for "${base.title}"`, 'success')
    }

    showAddCourseModal.value = false
    await loadData()
  } catch (e) {
    notify(e?.message || 'Save failed', 'error')
  } finally {
    isSubmittingCourse.value = false
  }
}

const removeCourse = async (course) => {
  const confirmed = window.confirm(`Delete "${course.title}"? This cannot be undone.`)
  if (!confirmed) return
  try {
    await deleteCourse(course.id)
    notify(`Deleted "${course.title}"`, 'success')
    await loadData()
  } catch (e) {
    notify(e?.message || 'Delete failed', 'error')
  }
}

const handleUpsertSave = async (payloadFromChild) => {
  await submitCourse(payloadFromChild)
}

const handleAssignSave = (payload) => {
  if (payload?.mode === 'group') {
    saveGroupAssignment(payload.groupId)
    return
  }
  assignForm.assignedUserIds = [...(payload?.assignedUserIds || [])]
  saveAssignment()
}
</script>

<template>
  <div class="min-h-screen bg-[#F7F5FA] p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-asi-black">Courses</h1>
        <p class="text-sm text-asi-gray mt-0.5">
          {{ loading ? 'Loading…' : `${courses.length} total courses` }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="loading"
          @click="openAddCourseModal"
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-[#462C6B] to-[#462C6B] hover:from-[#462C6B] hover:to-[#CA1F47] rounded-lg transition-all shadow-sm hover:shadow-md hover:shadow-[#462C6B]/30 disabled:opacity-50"
        >
          <BookPlus :size="15" />
          Add course
        </button>
      </div>
    </div>

    <div
      v-if="loadError"
      class="mb-5 rounded-xl border border-[#FAEAEE] bg-[#FAEAEE] text-[#CA1F47] px-4 py-3 text-sm"
    >
      {{ loadError }}
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-5">
      <div class="relative flex-1 min-w-[200px] max-w-sm">
        <Search
          :size="14"
          class="absolute left-3 top-1/2 -translate-y-1/2 text-[#7D6B9D]"
        />
        <input
          v-model="search"
          placeholder="Search courses..."
          class="w-full pl-9 pr-4 h-10 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] shadow-sm placeholder:text-[#7D6B9D]/60"
        />
      </div>

      <div class="relative">
        <select
          v-model="category"
          class="appearance-none h-10 pl-4 pr-9 text-sm bg-white border border-[#E8E2F0] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#462C6B]/20 focus:border-[#462C6B] text-[#231F20] cursor-pointer shadow-sm"
        >
          <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <ChevronDown :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-[#7D6B9D] pointer-events-none" />
      </div>
    </div>

    <!-- Loading skeletons -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div v-for="i in 8" :key="i" class="rounded-2xl overflow-hidden bg-white shadow-sm border border-[#E8E2F0]">
        <div class="h-40 bg-gradient-to-br from-[#E8E2F0] to-[#F0EDF6] animate-pulse" />
        <div class="p-4 space-y-3">
          <div class="h-3.5 rounded-full bg-[#F0EDF6] animate-pulse w-3/4" />
          <div class="h-3 rounded-full bg-[#F0EDF6] animate-pulse w-1/2" />
          <div class="h-8 rounded-xl bg-[#F0EDF6] animate-pulse mt-3" />
        </div>
      </div>
    </div>

    <!-- Course cards -->
    <div v-else-if="filtered.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="(course, idx) in filtered"
        :key="course.id"
        class="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:shadow-[#462C6B]/15 border border-[#E8E2F0] hover:border-[#7D6B9D]/30 transition-all duration-300 hover:-translate-y-1 flex flex-col"
      >
        <!-- Thumbnail -->
        <div class="relative h-40 overflow-hidden bg-gradient-to-br from-[#462C6B] to-[#CA1F47]">
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-white text-4xl font-bold">
              {{ course.title?.[0] || 'C' }}
            </div>
          </div>
          <div class="absolute top-3 left-3 right-3 flex items-center justify-between">
            <span
              v-if="course.contentType === 'scorm12'"
              class="text-[10px] font-bold px-2.5 py-1 rounded-full bg-black/40 text-white/90 backdrop-blur-sm uppercase tracking-wide"
            >
              SCORM 1.2
            </span>
            <span
              :class="clsx(
                'text-[10px] font-bold px-2.5 py-1 rounded-full backdrop-blur-sm',
                course.status === 'Published'
                  ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/30'
                  : 'bg-white/10 text-white/60 border border-white/20'
              )"
            >
              {{ course.status || 'Draft' }}
            </span>
          </div>
        </div>

        <!-- Card body -->
        <div class="p-4 flex flex-col flex-1">
          <h3 class="font-bold text-[#231F20] text-sm leading-snug line-clamp-2 mb-2 group-hover:text-[#462C6B] transition-colors">
            {{ course.title }}
          </h3>
          <div class="flex items-center gap-2 mb-3">
            <span class="inline-flex items-center text-[11px] font-semibold px-2.5 py-1 rounded-full bg-[#F0EDF6] text-[#462C6B]">
              {{ course.category || 'General' }}
            </span>
          </div>

          <div class="text-xs text-[#67686B] mb-4 space-y-1">
            <div v-if="course.code && course.code !== '-'">Code: {{ course.code }}</div>
            <div v-if="course.updatedAt">Updated: {{ course.updatedAt }}</div>
          </div>

          <!-- Action buttons -->
          <div class="mt-auto grid grid-cols-2 gap-2">
            <button
              type="button"
              class="flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#462C6B] to-[#462C6B] hover:from-[#462C6B] hover:to-[#CA1F47] hover:shadow-md hover:shadow-[#462C6B]/30 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
              @click="openEditCourseModal(course)"
              title="Edit course"
            >
              <Pencil :size="11" />
              Edit
            </button>
            <button
              type="button"
              :disabled="!canAssignCourse(course)"
              :class="clsx(
                'flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all duration-300',
                canAssignCourse(course)
                  ? 'text-[#462C6B] bg-[#F0EDF6] hover:bg-[#462C6B] hover:text-white hover:shadow-md hover:shadow-[#462C6B]/20 hover:scale-[1.02] active:scale-[0.98]'
                  : 'text-[#7D6B9D]/40 bg-[#F0EDF6]/50 cursor-not-allowed'
              )"
              @click="canAssignCourse(course) && openAssignModal(course)"
              :title="canAssignCourse(course) ? 'Assign learners' : 'Publish course to enable assignment'"
            >
              <UsersIcon :size="11" />
              Assign
            </button>
          </div>
          
          <div class="mt-2 grid grid-cols-2 gap-2">
            <button
              type="button"
              class="flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold text-[#462C6B] bg-[#F0EDF6] hover:bg-[#462C6B] hover:text-white hover:shadow-md hover:shadow-[#462C6B]/20 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
              @click="openLearnerPreview(course)"
              title="Preview as learner"
            >
              <Eye :size="11" />
              Preview
            </button>
            <button
              type="button"
              class="flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold text-red-600 bg-red-50 hover:bg-red-600 hover:text-white hover:shadow-md hover:shadow-red-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
              @click="removeCourse(course)"
              title="Delete course"
            >
              <Trash2 :size="11" />
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-dashed border-[#E8E2F0]">
      <div class="w-16 h-16 rounded-2xl bg-[#F0EDF6] flex items-center justify-center mb-4">
        <BookPlus :size="24" class="text-[#7D6B9D]" />
      </div>
      <h3 class="text-base font-bold text-[#231F20] mb-1">No courses found</h3>
      <p class="text-sm text-[#67686B] text-center max-w-xs">
        {{ search || category !== 'All' ? 'No courses match your search criteria.' : 'Get started by adding your first course.' }}
      </p>
      <button
        v-if="search || category !== 'All'"
        type="button"
        class="mt-4 text-xs font-bold text-[#462C6B] hover:text-[#CA1F47] transition-colors"
        @click="search = ''; category = 'All'"
      >
        Clear filters
      </button>
    </div>

    <CourseUpsertModal
      :open="showAddCourseModal"
      :mode="isEditMode ? 'edit' : 'create'"
      :categories="CATEGORIES"
      :initial-value="addCourseForm"
      :saving="isSubmittingCourse"
      @close="closeAddCourseModal"
      @save="handleUpsertSave"
    />

    <CourseAssignModal
      :open="showAssignModal"
      :course-title="assigningCourse?.title || ''"
      :users="assignableUsers"
      :initial-assigned-user-ids="assigningCourse?.assignedUserIds || []"
      :learner-assignments="assigningCourse?.learnerAssignments || []"
      :can-assign-to-group="isAdmin"
      :groups="groupsForAssignment"
      :groups-loading="groupsForAssignmentLoading"
      :groups-load-error="groupsForAssignmentError"
      :saving="isSubmittingAssignment"
      @close="closeAssignModal"
      @save="handleAssignSave"
    />

    <div
      v-if="showSnackbar"
      :class="clsx(
        'fixed bottom-6 right-6 z-[80] max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg',
        snackbarTone === 'error'
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-emerald-200 bg-emerald-50 text-emerald-700'
      )"
    >
      {{ snackbarMessage }}
    </div>
  </div>
</template>
