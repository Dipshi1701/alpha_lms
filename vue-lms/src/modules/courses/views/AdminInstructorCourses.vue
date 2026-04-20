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

const CATEGORIES = ['All', 'General', 'Sales', 'Management', 'Compliance', 'Technical']

const router = useRouter()

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

const addCourseForm = reactive({
  title: '',
  category: 'General',
  description: '',
  status: 'Draft',
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

const openAssignModal = (course) => {
  if (!canAssignCourse(course)) return
  assigningCourse.value = course
  assignForm.assignedUserIds = [...(course.assignedUserIds || [])]
  showAssignModal.value = true
}

const closeAssignModal = () => {
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
  if (!assigningCourse.value) return
  try {
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
  }
}

const submitCourse = async (payload) => {
  if (isSubmittingCourse.value) return
  isSubmittingCourse.value = true
  const isCreate = !isEditMode.value
  const scormFile = payload?.scormFile
  const base = {
    title: payload?.title?.trim() || 'Untitled course',
    category: payload?.category || 'General',
    description: (payload?.description || '').trim() || null,
    status: payload?.status || 'Draft',
    code: '-',
    price: '-',
  }

  try {
    let courseId
    if (isEditMode.value && editingCourseId.value != null) {
      courseId = editingCourseId.value
      await updateCourse(courseId, {
        title: base.title,
        category: base.category,
        description: base.description,
        status: base.status,
        code: base.code,
        price: base.price,
      })
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

const handleAssignSave = ({ assignedUserIds }) => {
  assignForm.assignedUserIds = [...(assignedUserIds || [])]
  saveAssignment()
}
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-gray-800">Courses</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ loading ? 'Loading…' : `${courses.length} total courses` }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          :disabled="loading"
          @click="openAddCourseModal"
          class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-all shadow-sm disabled:opacity-50"
        >
          <BookPlus :size="15" />
          Add course
        </button>
      </div>
    </div>

    <div
      v-if="loadError"
      class="mb-5 rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm"
    >
      {{ loadError }}
    </div>

    <div class="flex flex-wrap items-center gap-3 mb-5">
      <div class="relative flex-1 min-w-[200px] max-w-sm">
        <Search
          :size="15"
          class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        />
        <input
          v-model="search"
          placeholder="Search courses..."
          class="w-full pl-9 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
        />
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <button
          v-for="cat in CATEGORIES"
          :key="cat"
          type="button"
          @click="category = cat"
          :class="clsx(
            'px-3 py-1.5 text-xs font-medium rounded-full border transition-all',
            category === cat
              ? 'bg-[#1a3a5c] text-white border-[#1a3a5c]'
              : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
          )"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Course</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Code</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Category</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Price</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Last updated on</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="course in filtered"
              :key="course.id"
              class="border-b border-gray-100 hover:bg-gray-50/80"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <div
                    :class="clsx('w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold', course.color || 'bg-slate-400')"
                  >
                    {{ course.title?.[0] || 'C' }}
                  </div>
                  <div class="min-w-0">
                    <p class="font-semibold text-gray-900 truncate">{{ course.title }}</p>
                    <div class="flex items-center gap-2 mt-0.5">
                      <span
                        :class="clsx(
                          'text-xs font-semibold px-2 py-0.5 rounded-full',
                          course.status === 'Published'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        )"
                      >
                        {{ course.status || 'Inactive' }}
                      </span>
                      <span
                        v-if="course.contentType === 'scorm12'"
                        class="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-100"
                      >
                        SCORM 1.2
                      </span>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-600">{{ course.code || '-' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ course.category || '-' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ course.price || '-' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ course.updatedAt || '-' }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                    title="Preview as learner"
                    @click="openLearnerPreview(course)"
                  >
                    <Eye :size="16" />
                  </button>
                  <button
                    type="button"
                    :disabled="!canAssignCourse(course)"
                    :class="clsx(
                      'p-2 rounded-lg transition-colors',
                      canAssignCourse(course)
                        ? 'hover:bg-blue-50 text-blue-700'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    )"
                    :title="canAssignCourse(course) ? 'Assign learners' : 'Publish course to enable assignment'"
                    @click="openAssignModal(course)"
                  >
                    <UsersIcon :size="16" />
                  </button>
                  <button
                    type="button"
                    class="p-2 rounded-lg hover:bg-gray-100 text-gray-700"
                    title="Edit"
                    @click="openEditCourseModal(course)"
                  >
                    <Pencil :size="16" />
                  </button>
                  <button
                    type="button"
                    class="p-2 rounded-lg hover:bg-red-50 text-red-700"
                    title="Delete"
                    @click="removeCourse(course)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="6" class="px-4 py-10 text-center text-sm text-gray-500">
                No courses found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
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
