<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Users2, Plus, Pencil, Trash2, Eye, Loader2 } from 'lucide-vue-next'
import { useAccess } from '../../../composables/useAccess'
import GroupFormModal from '../modals/GroupFormModal.vue'
import { fetchGroups, createGroup, updateGroup, deleteGroup } from '../service'

const router = useRouter()
const { isAdmin } = useAccess()

const groups = ref([])
const loading = ref(true)
const loadError = ref('')

const showModal = ref(false)
const modalMode = ref('create') // 'create' | 'edit'
const editingGroup = ref(null)
const saving = ref(false)
const modalError = ref('')

const snackbarMessage = ref('')
const snackbarTone = ref('success') // success | error
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

const loadGroups = async () => {
  loading.value = true
  loadError.value = ''
  try {
    // The backend is responsible for scope: Administrators receive every
    // group, a scoped Instructor receives only groups they manage. This
    // page simply renders whatever GET /api/groups returns.
    groups.value = await fetchGroups()
  } catch (e) {
    loadError.value = e?.message || 'Failed to load groups'
    groups.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadGroups)
onBeforeUnmount(() => {
  if (snackbarTimer) clearTimeout(snackbarTimer)
})

const openCreateModal = () => {
  modalMode.value = 'create'
  editingGroup.value = null
  modalError.value = ''
  showModal.value = true
}

const openEditModal = (group) => {
  modalMode.value = 'edit'
  editingGroup.value = group
  modalError.value = ''
  showModal.value = true
}

const closeModal = () => {
  if (saving.value) return
  showModal.value = false
}

const handleSave = async ({ name }) => {
  saving.value = true
  modalError.value = ''
  try {
    if (modalMode.value === 'edit' && editingGroup.value) {
      await updateGroup(editingGroup.value.id, { name })
      notify(`Updated "${name}"`, 'success')
    } else {
      await createGroup({ name })
      notify(`Created "${name}"`, 'success')
    }
    showModal.value = false
    await loadGroups()
  } catch (e) {
    modalError.value = e?.message || 'Save failed'
  } finally {
    saving.value = false
  }
}

const removeGroup = async (group) => {
  const confirmed = window.confirm(`Delete "${group.name}"? This cannot be undone.`)
  if (!confirmed) return
  try {
    await deleteGroup(group.id)
    notify(`Deleted "${group.name}"`, 'success')
    await loadGroups()
  } catch (e) {
    notify(e?.message || 'Delete failed', 'error')
  }
}

const viewGroup = (group) => {
  router.push({ name: 'group-detail', params: { groupId: String(group.id) } })
}

const hasRows = computed(() => groups.value.length > 0)
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-asi-black">Groups</h1>
        <p class="text-sm text-asi-gray mt-0.5">
          {{ isAdmin ? 'Manage learner groups, group managers and group course assignments.' : 'Groups you manage.' }}
        </p>
      </div>
      <button
        v-if="isAdmin"
        type="button"
        data-testid="create-group-btn"
        :disabled="loading"
        @click="openCreateModal"
        class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-asi-purple text-white text-sm font-semibold hover:bg-[#5a3a8a] shadow-sm transition-colors disabled:opacity-50"
      >
        <Plus :size="16" />
        Create group
      </button>
    </div>

    <div
      v-if="loadError"
      class="mb-5 rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm"
    >
      {{ loadError }}
    </div>

    <div class="bg-white rounded-2xl border border-asi-border shadow-sm overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20 text-asi-gray gap-2">
        <Loader2 :size="22" class="animate-spin" />
        Loading groups…
      </div>

      <div v-else-if="!hasRows" class="py-16 text-center text-asi-gray text-sm px-6">
        <Users2 :size="28" class="mx-auto mb-3 text-asi-border" />
        <p v-if="isAdmin">
          No groups yet. Click <strong>Create group</strong> to add one.
        </p>
        <p v-else>
          No groups assigned to you yet.
        </p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-asi-surface border-b border-asi-border">
            <tr>
              <th class="text-left px-4 py-3 font-semibold text-asi-black">Group</th>
              <th class="text-left px-4 py-3 font-semibold text-asi-black">Created</th>
              <th class="text-right px-4 py-3 font-semibold text-asi-black">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="group in groups"
              :key="group.id"
              class="border-b border-asi-border hover:bg-asi-surface"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold bg-asi-purple">
                    {{ group.name?.[0] || 'G' }}
                  </div>
                  <p class="font-semibold text-asi-black truncate">{{ group.name }}</p>
                </div>
              </td>
              <td class="px-4 py-3 text-asi-gray">{{ formatDate(group.createdAt) }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    data-testid="view-group-btn"
                    class="p-2 rounded-lg hover:bg-asi-surface text-asi-gray"
                    title="View group"
                    @click="viewGroup(group)"
                  >
                    <Eye :size="16" />
                  </button>
                  <button
                    v-if="isAdmin"
                    type="button"
                    data-testid="edit-group-btn"
                    class="p-2 rounded-lg hover:bg-asi-surface text-asi-gray"
                    title="Edit"
                    @click="openEditModal(group)"
                  >
                    <Pencil :size="16" />
                  </button>
                  <button
                    v-if="isAdmin"
                    type="button"
                    data-testid="delete-group-btn"
                    class="p-2 rounded-lg hover:bg-red-50 text-red-700"
                    title="Delete"
                    @click="removeGroup(group)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <GroupFormModal
      :open="showModal"
      :mode="modalMode"
      :initial-value="editingGroup || {}"
      :saving="saving"
      :api-error="modalError"
      @close="closeModal"
      @save="handleSave"
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
