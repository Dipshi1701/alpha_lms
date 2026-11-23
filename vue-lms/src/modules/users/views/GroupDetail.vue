<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Loader2, ShieldAlert, UserPlus, Users2, BookOpen, Trash2, Pencil, Search, X,
} from 'lucide-vue-next'
import { useAccess } from '../../../composables/useAccess'
import GroupFormModal from '../modals/GroupFormModal.vue'
import {
  fetchGroup, updateGroup, deleteGroup,
  fetchAssignableLearners, fetchGroupMembers, addGroupMember, removeGroupMember,
  fetchAssignableInstructors, fetchGroupManagers, assignGroupManager, removeGroupManager,
  fetchGroupCourses, fetchAssignableCourses, assignGroupCourse, removeGroupCourse,
  fetchUsers,
} from '../service'

const route = useRoute()
const router = useRouter()
const { isAdmin } = useAccess()

const groupId = computed(() => route.params.groupId)

const group = ref(null)
const loading = ref(true)
// 'notfound' | 'forbidden' | 'error' | ''
const loadErrorKind = ref('')
const loadErrorMessage = ref('')

const usersById = ref({})

const snackbarMessage = ref('')
const snackbarTone = ref('success')
const showSnackbar = ref(false)
let snackbarTimer = null

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

const formatDate = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

const creatorLabel = computed(() => {
  if (!group.value?.createdById) return '—'
  const found = usersById.value[group.value.createdById]
  return found ? found.full_name || found.email : `User #${group.value.createdById}`
})

const loadGroup = async () => {
  loading.value = true
  loadErrorKind.value = ''
  loadErrorMessage.value = ''
  try {
    group.value = await fetchGroup(groupId.value)
  } catch (e) {
    group.value = null
    if (e?.status === 403) {
      loadErrorKind.value = 'forbidden'
      loadErrorMessage.value = "You don't have access to this group."
    } else if (e?.status === 404) {
      loadErrorKind.value = 'notfound'
      loadErrorMessage.value = 'Group not found.'
    } else {
      loadErrorKind.value = 'error'
      loadErrorMessage.value = e?.message || 'Failed to load this group.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadGroup()
  if (group.value) loadOverviewCounts()
  if (isAdmin.value && group.value) {
    try {
      const rows = await fetchUsers()
      usersById.value = Object.fromEntries(rows.map((u) => [u.id, u]))
    } catch {
      // Non-critical — creator name simply falls back to "User #<id>".
    }
  }
})

const goBack = () => router.push({ path: '/groups' })

// ── Tabs ──────────────────────────────────────────────────────────────────
const TABS = ['Overview', 'Members', 'Managers', 'Courses']
const activeTab = ref('Overview')

// ── Edit / Delete (Admin only) ───────────────────────────────────────────
const showEditModal = ref(false)
const savingEdit = ref(false)
const editError = ref('')

const openEdit = () => {
  editError.value = ''
  showEditModal.value = true
}
const closeEdit = () => {
  if (!savingEdit.value) showEditModal.value = false
}
const saveEdit = async ({ name }) => {
  savingEdit.value = true
  editError.value = ''
  try {
    group.value = await updateGroup(groupId.value, { name })
    notify(`Updated "${name}"`, 'success')
    showEditModal.value = false
  } catch (e) {
    editError.value = e?.message || 'Save failed'
  } finally {
    savingEdit.value = false
  }
}

const removeThisGroup = async () => {
  if (!group.value) return
  const confirmed = window.confirm(`Delete "${group.value.name}"? This cannot be undone.`)
  if (!confirmed) return
  try {
    await deleteGroup(groupId.value)
    notify(`Deleted "${group.value.name}"`, 'success')
    router.push({ path: '/groups' })
  } catch (e) {
    notify(e?.message || 'Delete failed', 'error')
  }
}

// ── Members tab ──────────────────────────────────────────────────────────
const members = ref([])
const membersLoading = ref(false)
const membersLoadError = ref('')
const memberQuery = ref('')
const learnerOptions = ref([])
const learnersLoading = ref(false)
const learnersLoadError = ref('')
const showAddMembers = ref(false)
const addMemberQuery = ref('')
const selectedMemberIds = ref([])
const memberActionError = ref('')
const memberActionBusy = ref(false)

const memberIds = computed(() => new Set(members.value.map((m) => m.userId)))

const filteredMembers = computed(() => {
  const q = memberQuery.value.trim().toLowerCase()
  if (!q) return members.value
  return members.value.filter((m) =>
    m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
  )
})

const availableLearners = computed(() => {
  const q = addMemberQuery.value.trim().toLowerCase()
  return learnerOptions.value.filter((u) => {
    if (memberIds.value.has(u.id)) return false
    if (!q) return true
    return u.name.toLowerCase().includes(q)
  })
})

const loadMembers = async () => {
  membersLoading.value = true
  membersLoadError.value = ''
  try {
    members.value = await fetchGroupMembers(groupId.value)
  } catch (e) {
    membersLoadError.value = e?.message || 'Failed to load members'
    members.value = []
  } finally {
    membersLoading.value = false
  }
}

const loadLearnerOptions = async () => {
  if (!isAdmin.value) return
  learnersLoading.value = true
  learnersLoadError.value = ''
  try {
    learnerOptions.value = await fetchAssignableLearners()
  } catch (e) {
    learnersLoadError.value = e?.message || 'Failed to load learners'
  } finally {
    learnersLoading.value = false
  }
}

const openAddMembers = async () => {
  memberActionError.value = ''
  addMemberQuery.value = ''
  selectedMemberIds.value = []
  showAddMembers.value = true
  if (learnerOptions.value.length === 0) await loadLearnerOptions()
}

const closeAddMembers = () => {
  if (!memberActionBusy.value) showAddMembers.value = false
}

const toggleSelectedMember = (userId) => {
  if (memberActionBusy.value) return
  if (selectedMemberIds.value.includes(userId)) {
    selectedMemberIds.value = selectedMemberIds.value.filter((id) => id !== userId)
    return
  }
  selectedMemberIds.value = [...selectedMemberIds.value, userId]
}

const addSelectedMembers = async () => {
  if (!selectedMemberIds.value.length) return
  memberActionBusy.value = true
  memberActionError.value = ''
  const ids = [...selectedMemberIds.value]
  try {
    for (const userId of ids) {
      await addGroupMember(groupId.value, userId)
    }
    const count = ids.length
    notify(count === 1 ? 'Learner added to group' : `${count} learners added to group`, 'success')
    selectedMemberIds.value = []
    showAddMembers.value = false
    await loadMembers()
  } catch (e) {
    memberActionError.value = e?.message || 'Could not add learner'
    await loadMembers()
  } finally {
    memberActionBusy.value = false
  }
}

const removeMember = async (member) => {
  const confirmed = window.confirm(`Remove "${member.name}" from this group?`)
  if (!confirmed) return
  memberActionBusy.value = true
  memberActionError.value = ''
  try {
    await removeGroupMember(groupId.value, member.userId)
    notify('Learner removed from group', 'success')
    await loadMembers()
  } catch (e) {
    memberActionError.value = e?.message || 'Could not remove learner'
  } finally {
    memberActionBusy.value = false
  }
}

// ── Managers tab ─────────────────────────────────────────────────────────
const managers = ref([])
const managersLoading = ref(false)
const managersLoadError = ref('')
const managerQuery = ref('')
const instructorOptions = ref([])
const instructorsLoading = ref(false)
const instructorsLoadError = ref('')
const showAddManagers = ref(false)
const addManagerQuery = ref('')
const selectedManagerIds = ref([])
const managerActionError = ref('')
const managerActionBusy = ref(false)

const managerIds = computed(() => new Set(managers.value.map((m) => m.userId)))

const filteredManagers = computed(() => {
  const q = managerQuery.value.trim().toLowerCase()
  if (!q) return managers.value
  return managers.value.filter((m) =>
    m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
  )
})

const availableInstructors = computed(() => {
  const q = addManagerQuery.value.trim().toLowerCase()
  return instructorOptions.value.filter((u) => {
    if (managerIds.value.has(u.id)) return false
    if (!q) return true
    return u.name.toLowerCase().includes(q) || (u.email || '').toLowerCase().includes(q)
  })
})

const loadManagers = async () => {
  managersLoading.value = true
  managersLoadError.value = ''
  try {
    managers.value = await fetchGroupManagers(groupId.value)
  } catch (e) {
    managersLoadError.value = e?.message || 'Failed to load managers'
    managers.value = []
  } finally {
    managersLoading.value = false
  }
}

const loadInstructorOptions = async () => {
  if (!isAdmin.value) return
  instructorsLoading.value = true
  instructorsLoadError.value = ''
  try {
    instructorOptions.value = await fetchAssignableInstructors()
  } catch (e) {
    instructorsLoadError.value = e?.message || 'Failed to load instructors'
  } finally {
    instructorsLoading.value = false
  }
}

const openAddManagers = async () => {
  managerActionError.value = ''
  addManagerQuery.value = ''
  selectedManagerIds.value = []
  showAddManagers.value = true
  if (instructorOptions.value.length === 0) await loadInstructorOptions()
}

const closeAddManagers = () => {
  if (!managerActionBusy.value) showAddManagers.value = false
}

const toggleSelectedManager = (userId) => {
  if (managerActionBusy.value) return
  if (selectedManagerIds.value.includes(userId)) {
    selectedManagerIds.value = selectedManagerIds.value.filter((id) => id !== userId)
    return
  }
  selectedManagerIds.value = [...selectedManagerIds.value, userId]
}

const addSelectedManagers = async () => {
  if (!selectedManagerIds.value.length) return
  managerActionBusy.value = true
  managerActionError.value = ''
  const ids = [...selectedManagerIds.value]
  try {
    for (const userId of ids) {
      await assignGroupManager(groupId.value, userId)
    }
    const count = ids.length
    notify(count === 1 ? 'Instructor assigned as group manager' : `${count} instructors assigned as managers`, 'success')
    selectedManagerIds.value = []
    showAddManagers.value = false
    await loadManagers()
  } catch (e) {
    managerActionError.value = e?.message || 'Could not assign manager'
    await loadManagers()
  } finally {
    managerActionBusy.value = false
  }
}

const removeManager = async (manager) => {
  const confirmed = window.confirm(`Remove "${manager.name}" as a manager of this group?`)
  if (!confirmed) return
  managerActionBusy.value = true
  managerActionError.value = ''
  try {
    await removeGroupManager(groupId.value, manager.userId)
    notify('Group manager removed', 'success')
    await loadManagers()
  } catch (e) {
    managerActionError.value = e?.message || 'Could not remove manager'
  } finally {
    managerActionBusy.value = false
  }
}

// ── Courses tab (list is available to Admin + scoped Instructor) ─────────
const groupCourses = ref([])
const coursesLoading = ref(false)
const coursesLoadError = ref('')
const courseQuery = ref('')
const assignableCourses = ref([])
const showAddCourses = ref(false)
const addCourseQuery = ref('')
const selectedCourseIds = ref([])
const courseActionError = ref('')
const courseActionBusy = ref(false)

const filteredCourses = computed(() => {
  const q = courseQuery.value.trim().toLowerCase()
  if (!q) return groupCourses.value
  return groupCourses.value.filter((c) =>
    (c.title || '').toLowerCase().includes(q) || (c.category || '').toLowerCase().includes(q)
  )
})

const availableToAssign = computed(() => {
  const assignedIds = new Set(groupCourses.value.map((c) => c.id))
  const q = addCourseQuery.value.trim().toLowerCase()
  return assignableCourses.value.filter((c) => {
    if (assignedIds.has(c.id)) return false
    if (!q) return true
    return (c.title || '').toLowerCase().includes(q)
  })
})

const loadCourses = async () => {
  coursesLoading.value = true
  coursesLoadError.value = ''
  try {
    groupCourses.value = await fetchGroupCourses(groupId.value)
    if (isAdmin.value) {
      assignableCourses.value = await fetchAssignableCourses()
    }
  } catch (e) {
    coursesLoadError.value = e?.message || 'Failed to load group courses'
  } finally {
    coursesLoading.value = false
  }
}

const openAddCourses = async () => {
  courseActionError.value = ''
  addCourseQuery.value = ''
  selectedCourseIds.value = []
  showAddCourses.value = true
  if (isAdmin.value && assignableCourses.value.length === 0) {
    try {
      assignableCourses.value = await fetchAssignableCourses()
    } catch (e) {
      courseActionError.value = e?.message || 'Failed to load courses'
    }
  }
}

const closeAddCourses = () => {
  if (!courseActionBusy.value) showAddCourses.value = false
}

const toggleSelectedCourse = (courseId) => {
  if (courseActionBusy.value) return
  if (selectedCourseIds.value.includes(courseId)) {
    selectedCourseIds.value = selectedCourseIds.value.filter((id) => id !== courseId)
    return
  }
  selectedCourseIds.value = [...selectedCourseIds.value, courseId]
}

const addSelectedCourses = async () => {
  if (!selectedCourseIds.value.length) return
  courseActionBusy.value = true
  courseActionError.value = ''
  const ids = [...selectedCourseIds.value]
  try {
    for (const courseId of ids) {
      await assignGroupCourse(groupId.value, courseId)
    }
    const count = ids.length
    notify(count === 1 ? 'Course assigned to group' : `${count} courses assigned to group`, 'success')
    selectedCourseIds.value = []
    showAddCourses.value = false
    await loadCourses()
  } catch (e) {
    courseActionError.value = e?.message || 'Could not assign course'
    await loadCourses()
  } finally {
    courseActionBusy.value = false
  }
}

const removeCourseFromGroup = async (course) => {
  const confirmed = window.confirm(`Remove "${course.title}" from this group?`)
  if (!confirmed) return
  try {
    await removeGroupCourse(groupId.value, course.id)
    notify(`Removed "${course.title}" from group`, 'success')
    await loadCourses()
  } catch (e) {
    notify(e?.message || 'Could not remove course', 'error')
  }
}

const loadOverviewCounts = async () => {
  await Promise.all([loadMembers(), loadManagers(), loadCourses()])
}

watch(activeTab, (tab) => {
  if (!group.value) return
  if (tab === 'Overview') loadOverviewCounts()
  if (tab === 'Members') {
    loadMembers()
    if (isAdmin.value && learnerOptions.value.length === 0) loadLearnerOptions()
  }
  if (tab === 'Managers') {
    loadManagers()
    if (isAdmin.value && instructorOptions.value.length === 0) loadInstructorOptions()
  }
  if (tab === 'Courses') loadCourses()
})
</script>

<template>
  <div class="p-6 w-full mx-auto">
    <button
      type="button"
      class="inline-flex items-center gap-1.5 text-sm text-asi-gray hover:text-asi-black mb-4"
      @click="goBack"
    >
      <ArrowLeft :size="15" />
      Back to Groups
    </button>

    <div v-if="loading" class="flex items-center justify-center py-24 text-asi-gray gap-2">
      <Loader2 :size="22" class="animate-spin" />
      Loading group…
    </div>

    <div
      v-else-if="loadErrorKind"
      data-testid="group-load-error"
      class="bg-white rounded-2xl border border-asi-border shadow-sm py-16 text-center"
    >
      <ShieldAlert :size="30" class="mx-auto mb-3 text-asi-red" />
      <p class="text-sm font-medium text-asi-black">{{ loadErrorMessage }}</p>
      <button
        type="button"
        class="mt-4 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a]"
        @click="goBack"
      >
        Back to Groups
      </button>
    </div>

    <div v-else-if="group">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h1 class="text-xl font-bold text-asi-black">{{ group.name }}</h1>
          <p class="text-sm text-asi-gray mt-0.5">
            Created {{ formatDate(group.createdAt) }} · by {{ creatorLabel }}
          </p>
        </div>
        <div v-if="isAdmin" class="flex items-center gap-2">
          <button
            type="button"
            data-testid="detail-edit-btn"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg border border-asi-border"
            @click="openEdit"
          >
            <Pencil :size="14" />
            Edit
          </button>
          <button
            type="button"
            data-testid="detail-delete-btn"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 rounded-lg border border-red-200"
            @click="removeThisGroup"
          >
            <Trash2 :size="14" />
            Delete
          </button>
        </div>
      </div>

      <div class="flex items-center gap-1 mb-5 border-b border-asi-border">
        <button
          v-for="tab in TABS"
          :key="tab"
          type="button"
          :data-testid="`tab-${tab}`"
          :class="[
            'px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors',
            activeTab === tab
              ? 'border-asi-purple text-asi-purple'
              : 'border-transparent text-asi-gray hover:text-asi-black',
          ]"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>

      <!-- Overview -->
      <div v-if="activeTab === 'Overview'" class="space-y-4">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <button
            type="button"
            class="bg-white rounded-2xl border border-asi-border shadow-sm p-5 text-left hover:border-asi-lavender transition-colors"
            @click="activeTab = 'Members'"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-asi-gray">Members</p>
                <p class="mt-2 text-2xl font-bold text-asi-black">{{ membersLoading ? '—' : members.length }}</p>
              </div>
              <div class="rounded-2xl p-3 bg-asi-purple-light">
                <Users2 :size="22" class="text-asi-purple" />
              </div>
            </div>
          </button>
          <button
            type="button"
            class="bg-white rounded-2xl border border-asi-border shadow-sm p-5 text-left hover:border-asi-lavender transition-colors"
            @click="activeTab = 'Managers'"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-asi-gray">Managers</p>
                <p class="mt-2 text-2xl font-bold text-asi-black">{{ managersLoading ? '—' : managers.length }}</p>
              </div>
              <div class="rounded-2xl p-3 bg-asi-orange-light">
                <UserPlus :size="22" class="text-asi-orange" />
              </div>
            </div>
          </button>
          <button
            type="button"
            class="bg-white rounded-2xl border border-asi-border shadow-sm p-5 text-left hover:border-asi-lavender transition-colors"
            @click="activeTab = 'Courses'"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-asi-gray">Courses</p>
                <p class="mt-2 text-2xl font-bold text-asi-black">{{ coursesLoading ? '—' : groupCourses.length }}</p>
              </div>
              <div class="rounded-2xl p-3 bg-asi-blue-light">
                <BookOpen :size="22" class="text-asi-blue" />
              </div>
            </div>
          </button>
        </div>

        <div class="bg-white rounded-2xl border border-asi-border shadow-sm p-6">
          <h2 class="text-base font-semibold text-asi-black mb-4">Group details</h2>
          <dl class="grid grid-cols-1 md:grid-cols-2 gap-5 text-sm">
            <div>
              <dt class="text-xs font-semibold text-asi-gray uppercase tracking-wide">Group ID</dt>
              <dd class="mt-1 text-asi-black">{{ group.id }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-asi-gray uppercase tracking-wide">Name</dt>
              <dd class="mt-1 text-asi-black">{{ group.name }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-asi-gray uppercase tracking-wide">Created</dt>
              <dd class="mt-1 text-asi-black">{{ formatDate(group.createdAt) }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-asi-gray uppercase tracking-wide">Created by</dt>
              <dd class="mt-1 text-asi-black">{{ creatorLabel }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Members -->
      <div v-else-if="activeTab === 'Members'" class="space-y-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-asi-black">Members</h2>
            <p class="text-sm text-asi-gray mt-0.5">
              Learners in this group. A learner can belong to more than one group.
            </p>
          </div>
          <button
            v-if="isAdmin"
            type="button"
            data-testid="add-members-btn"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-asi-purple text-white text-sm font-semibold hover:bg-[#5a3a8a] shadow-sm"
            @click="openAddMembers"
          >
            <UserPlus :size="16" />
            Add members
          </button>
        </div>

        <p v-if="!isAdmin" class="text-sm text-asi-gray">
          Only an Administrator can add or remove group members.
        </p>

        <div v-if="memberActionError && !showAddMembers" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ memberActionError }}
        </div>
        <div v-if="membersLoadError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ membersLoadError }}
        </div>

        <div class="bg-white rounded-2xl border border-asi-border shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-asi-border">
            <div class="relative max-w-sm">
              <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
              <input
                v-model="memberQuery"
                type="text"
                placeholder="Search members"
                class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
              />
            </div>
          </div>

          <div v-if="membersLoading" class="flex items-center justify-center py-16 text-asi-gray gap-2">
            <Loader2 :size="20" class="animate-spin" />
            Loading members…
          </div>

          <div v-else-if="members.length === 0" class="py-16 text-center text-sm text-asi-gray px-6">
            <UserPlus :size="28" class="mx-auto mb-3 text-asi-border" />
            <p>No members in this group yet.</p>
            <p v-if="isAdmin" class="mt-1">Click <strong>Add members</strong> to enroll learners.</p>
          </div>

          <div v-else-if="filteredMembers.length === 0" class="py-12 text-center text-sm text-asi-gray">
            No members match “{{ memberQuery }}”.
          </div>

          <div v-else class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-asi-surface border-b border-asi-border">
                <tr>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Learner</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Email</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Added</th>
                  <th v-if="isAdmin" class="text-right px-4 py-3 font-semibold text-asi-black">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="member in filteredMembers"
                  :key="member.userId"
                  class="border-b border-asi-border hover:bg-asi-surface"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold bg-asi-purple">
                        {{ member.name?.[0] || 'L' }}
                      </div>
                      <p class="font-semibold text-asi-black truncate">{{ member.name }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-asi-gray">{{ member.email || '—' }}</td>
                  <td class="px-4 py-3 text-asi-gray">{{ formatDate(member.addedAt) }}</td>
                  <td v-if="isAdmin" class="px-4 py-3 text-right">
                    <button
                      type="button"
                      class="p-2 rounded-lg hover:bg-red-50 text-red-700"
                      title="Remove from group"
                      :disabled="memberActionBusy"
                      :data-testid="`remove-member-${member.userId}`"
                      @click="removeMember(member)"
                    >
                      <Trash2 :size="15" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div
            v-if="showAddMembers"
            class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
            @click.self="closeAddMembers"
          >
            <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
              <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
                <div>
                  <h2 class="text-base font-semibold text-asi-black">Add members</h2>
                  <p class="text-xs text-asi-gray mt-0.5">{{ group.name }}</p>
                </div>
                <button
                  type="button"
                  class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray"
                  :disabled="memberActionBusy"
                  @click="closeAddMembers"
                >
                  <X :size="18" />
                </button>
              </div>

              <div class="p-6 space-y-4 overflow-y-auto min-h-[200px]">
                <div v-if="memberActionError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {{ memberActionError }}
                </div>
                <div v-if="learnersLoadError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {{ learnersLoadError }}
                </div>

                <div class="relative">
                  <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
                  <input
                    v-model="addMemberQuery"
                    type="text"
                    placeholder="Search learners"
                    class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
                  />
                </div>

                <div v-if="learnersLoading" class="flex items-center justify-center py-10 text-asi-gray gap-2">
                  <Loader2 :size="18" class="animate-spin" />
                  Loading learners…
                </div>
                <div v-else-if="availableLearners.length === 0" class="py-10 text-center text-sm text-asi-gray">
                  No learners left to add.
                </div>
                <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <button
                    v-for="u in availableLearners"
                    :key="u.id"
                    type="button"
                    :data-testid="`pick-learner-${u.id}`"
                    class="flex items-center justify-between gap-2 border border-asi-border rounded-lg px-3 py-2 text-left hover:border-asi-lavender"
                    :disabled="memberActionBusy"
                    @click="toggleSelectedMember(u.id)"
                  >
                    <div class="min-w-0">
                      <p class="text-sm font-medium text-asi-black truncate">{{ u.name }}</p>
                      <p class="text-xs text-asi-gray">Learner</p>
                    </div>
                    <span
                      :class="[
                        'inline-flex items-center text-xs font-semibold px-2 py-1 rounded-md border flex-shrink-0',
                        selectedMemberIds.includes(u.id)
                          ? 'bg-asi-purple text-white border-asi-purple'
                          : 'bg-white text-asi-gray border-asi-border',
                      ]"
                    >
                      {{ selectedMemberIds.includes(u.id) ? 'Selected' : 'Add' }}
                    </span>
                  </button>
                </div>
              </div>

              <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
                <button
                  type="button"
                  class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg"
                  :disabled="memberActionBusy"
                  @click="closeAddMembers"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  data-testid="confirm-add-members"
                  class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] disabled:opacity-60"
                  :disabled="memberActionBusy || selectedMemberIds.length === 0"
                  @click="addSelectedMembers"
                >
                  <Loader2 v-if="memberActionBusy" :size="15" class="animate-spin" />
                  {{ memberActionBusy ? 'Adding…' : `Add ${selectedMemberIds.length || ''}`.trim() }}
                </button>
              </div>
            </div>
          </div>
      </div>

      <!-- Managers -->
      <div v-else-if="activeTab === 'Managers'" class="space-y-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-asi-black">Managers</h2>
            <p class="text-sm text-asi-gray mt-0.5">
              Instructors who can manage this group. There is no separate manager role.
            </p>
          </div>
          <button
            v-if="isAdmin"
            type="button"
            data-testid="add-managers-btn"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-asi-purple text-white text-sm font-semibold hover:bg-[#5a3a8a] shadow-sm"
            @click="openAddManagers"
          >
            <UserPlus :size="16" />
            Add managers
          </button>
        </div>

        <p v-if="!isAdmin" class="text-sm text-asi-gray">
          Only an Administrator can assign or remove group managers.
        </p>
        <div v-if="managerActionError && !showAddManagers" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ managerActionError }}
        </div>
        <div v-if="managersLoadError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ managersLoadError }}
        </div>

        <div class="bg-white rounded-2xl border border-asi-border shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-asi-border">
            <div class="relative max-w-sm">
              <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
              <input
                v-model="managerQuery"
                type="text"
                placeholder="Search managers"
                class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
              />
            </div>
          </div>
          <div v-if="managersLoading" class="flex items-center justify-center py-16 text-asi-gray gap-2">
            <Loader2 :size="20" class="animate-spin" />
            Loading managers…
          </div>
          <div v-else-if="managers.length === 0" class="py-16 text-center text-sm text-asi-gray px-6">
            <UserPlus :size="28" class="mx-auto mb-3 text-asi-border" />
            <p>No managers assigned yet.</p>
            <p v-if="isAdmin" class="mt-1">Click <strong>Add managers</strong> to assign instructors.</p>
          </div>
          <div v-else-if="filteredManagers.length === 0" class="py-12 text-center text-sm text-asi-gray">
            No managers match “{{ managerQuery }}”.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-asi-surface border-b border-asi-border">
                <tr>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Instructor</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Email</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Assigned</th>
                  <th v-if="isAdmin" class="text-right px-4 py-3 font-semibold text-asi-black">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="manager in filteredManagers"
                  :key="manager.userId"
                  class="border-b border-asi-border hover:bg-asi-surface"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold bg-asi-purple">
                        {{ manager.name?.[0] || 'I' }}
                      </div>
                      <p class="font-semibold text-asi-black truncate">{{ manager.name }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-asi-gray">{{ manager.email || '—' }}</td>
                  <td class="px-4 py-3 text-asi-gray">{{ formatDate(manager.assignedAt) }}</td>
                  <td v-if="isAdmin" class="px-4 py-3 text-right">
                    <button
                      type="button"
                      class="p-2 rounded-lg hover:bg-red-50 text-red-700"
                      title="Remove manager"
                      :disabled="managerActionBusy"
                      @click="removeManager(manager)"
                    >
                      <Trash2 :size="15" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div
          v-if="showAddManagers"
          class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
          @click.self="closeAddManagers"
        >
          <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
            <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
              <div>
                <h2 class="text-base font-semibold text-asi-black">Add managers</h2>
                <p class="text-xs text-asi-gray mt-0.5">{{ group.name }}</p>
              </div>
              <button type="button" class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray" :disabled="managerActionBusy" @click="closeAddManagers">
                <X :size="18" />
              </button>
            </div>
            <div class="p-6 space-y-4 overflow-y-auto min-h-[200px]">
              <div v-if="managerActionError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {{ managerActionError }}
              </div>
              <div v-if="instructorsLoadError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {{ instructorsLoadError }}
              </div>
              <div class="relative">
                <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
                <input
                  v-model="addManagerQuery"
                  type="text"
                  placeholder="Search instructors"
                  class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
                />
              </div>
              <div v-if="instructorsLoading" class="flex items-center justify-center py-10 text-asi-gray gap-2">
                <Loader2 :size="18" class="animate-spin" />
                Loading instructors…
              </div>
              <div v-else-if="availableInstructors.length === 0" class="py-10 text-center text-sm text-asi-gray">
                No instructors left to add.
              </div>
              <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <button
                  v-for="u in availableInstructors"
                  :key="u.id"
                  type="button"
                  class="flex items-center justify-between gap-2 border border-asi-border rounded-lg px-3 py-2 text-left hover:border-asi-lavender"
                  :disabled="managerActionBusy"
                  @click="toggleSelectedManager(u.id)"
                >
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-asi-black truncate">{{ u.name }}</p>
                    <p class="text-xs text-asi-gray truncate">{{ u.email || 'Instructor' }}</p>
                  </div>
                  <span
                    :class="[
                      'inline-flex items-center text-xs font-semibold px-2 py-1 rounded-md border flex-shrink-0',
                      selectedManagerIds.includes(u.id)
                        ? 'bg-asi-purple text-white border-asi-purple'
                        : 'bg-white text-asi-gray border-asi-border',
                    ]"
                  >
                    {{ selectedManagerIds.includes(u.id) ? 'Selected' : 'Add' }}
                  </span>
                </button>
              </div>
            </div>
            <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
              <button type="button" class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg" :disabled="managerActionBusy" @click="closeAddManagers">
                Cancel
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] disabled:opacity-60"
                :disabled="managerActionBusy || selectedManagerIds.length === 0"
                @click="addSelectedManagers"
              >
                <Loader2 v-if="managerActionBusy" :size="15" class="animate-spin" />
                {{ managerActionBusy ? 'Adding…' : `Add ${selectedManagerIds.length || ''}`.trim() }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Courses -->
      <div v-else-if="activeTab === 'Courses'" class="space-y-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-asi-black">Courses</h2>
            <p class="text-sm text-asi-gray mt-0.5">
              Published courses assigned to every current learner in this group.
            </p>
          </div>
          <button
            v-if="isAdmin"
            type="button"
            data-testid="add-courses-btn"
            class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-asi-purple text-white text-sm font-semibold hover:bg-[#5a3a8a] shadow-sm"
            @click="openAddCourses"
          >
            <BookOpen :size="16" />
            Assign courses
          </button>
        </div>

        <div v-if="coursesLoadError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ coursesLoadError }}
        </div>
        <div v-if="courseActionError && !showAddCourses" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ courseActionError }}
        </div>

        <div class="bg-white rounded-2xl border border-asi-border shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-asi-border">
            <div class="relative max-w-sm">
              <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
              <input
                v-model="courseQuery"
                type="text"
                placeholder="Search courses"
                class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
              />
            </div>
          </div>
          <div v-if="coursesLoading" class="flex items-center justify-center py-16 text-asi-gray gap-2">
            <Loader2 :size="20" class="animate-spin" />
            Loading courses…
          </div>
          <div v-else-if="groupCourses.length === 0" class="py-16 text-center text-sm text-asi-gray px-6">
            <BookOpen :size="28" class="mx-auto mb-3 text-asi-border" />
            <p>No courses assigned to this group yet.</p>
            <p v-if="isAdmin" class="mt-1">Click <strong>Assign courses</strong> to add published courses.</p>
          </div>
          <div v-else-if="filteredCourses.length === 0" class="py-12 text-center text-sm text-asi-gray">
            No courses match “{{ courseQuery }}”.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-asi-surface border-b border-asi-border">
                <tr>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Course</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Category</th>
                  <th class="text-left px-4 py-3 font-semibold text-asi-black">Status</th>
                  <th v-if="isAdmin" class="text-right px-4 py-3 font-semibold text-asi-black">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="course in filteredCourses"
                  :key="course.id"
                  class="border-b border-asi-border hover:bg-asi-surface"
                >
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                      <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold bg-asi-purple">
                        {{ course.title?.[0] || 'C' }}
                      </div>
                      <p class="font-semibold text-asi-black truncate">{{ course.title }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-asi-gray">{{ course.category || '—' }}</td>
                  <td class="px-4 py-3 text-asi-gray">{{ course.status }}</td>
                  <td v-if="isAdmin" class="px-4 py-3 text-right">
                    <button
                      type="button"
                      class="p-2 rounded-lg hover:bg-red-50 text-red-700"
                      title="Remove from group"
                      :disabled="courseActionBusy"
                      @click="removeCourseFromGroup(course)"
                    >
                      <Trash2 :size="15" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div
          v-if="showAddCourses"
          class="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
          @click.self="closeAddCourses"
        >
          <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
            <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
              <div>
                <h2 class="text-base font-semibold text-asi-black">Assign courses</h2>
                <p class="text-xs text-asi-gray mt-0.5">{{ group.name }}</p>
              </div>
              <button type="button" class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray" :disabled="courseActionBusy" @click="closeAddCourses">
                <X :size="18" />
              </button>
            </div>
            <div class="p-6 space-y-4 overflow-y-auto min-h-[200px]">
              <div v-if="courseActionError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {{ courseActionError }}
              </div>
              <div class="relative">
                <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-asi-gray" />
                <input
                  v-model="addCourseQuery"
                  type="text"
                  placeholder="Search published courses"
                  class="w-full pl-9 pr-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20"
                />
              </div>
              <div v-if="availableToAssign.length === 0" class="py-10 text-center text-sm text-asi-gray">
                No published courses left to assign.
              </div>
              <div v-else class="space-y-2">
                <button
                  v-for="c in availableToAssign"
                  :key="c.id"
                  type="button"
                  class="w-full flex items-center justify-between gap-2 border border-asi-border rounded-lg px-3 py-2 text-left hover:border-asi-lavender"
                  :disabled="courseActionBusy"
                  @click="toggleSelectedCourse(c.id)"
                >
                  <p class="text-sm font-medium text-asi-black truncate">{{ c.title }}</p>
                  <span
                    :class="[
                      'inline-flex items-center text-xs font-semibold px-2 py-1 rounded-md border flex-shrink-0',
                      selectedCourseIds.includes(c.id)
                        ? 'bg-asi-purple text-white border-asi-purple'
                        : 'bg-white text-asi-gray border-asi-border',
                    ]"
                  >
                    {{ selectedCourseIds.includes(c.id) ? 'Selected' : 'Assign' }}
                  </span>
                </button>
              </div>
            </div>
            <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
              <button type="button" class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg" :disabled="courseActionBusy" @click="closeAddCourses">
                Cancel
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] disabled:opacity-60"
                :disabled="courseActionBusy || selectedCourseIds.length === 0"
                @click="addSelectedCourses"
              >
                <Loader2 v-if="courseActionBusy" :size="15" class="animate-spin" />
                {{ courseActionBusy ? 'Assigning…' : `Assign ${selectedCourseIds.length || ''}`.trim() }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <GroupFormModal
      :open="showEditModal"
      mode="edit"
      :initial-value="group || {}"
      :saving="savingEdit"
      :api-error="editError"
      @close="closeEdit"
      @save="saveEdit"
    />

    <div
      v-if="showSnackbar"
      :class="[
        'fixed bottom-6 right-6 z-[80] max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg',
        snackbarTone === 'error'
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-emerald-200 bg-emerald-50 text-emerald-700',
      ]"
    >
      {{ snackbarMessage }}
    </div>
  </div>
</template>
