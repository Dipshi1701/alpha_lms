<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Users as UsersIcon, Plus, X, Loader2, Shield } from 'lucide-vue-next'
import { createUser, fetchUsers } from '../service'
import { ROLES } from '../../../composables/useAccess'

const loading = ref(true)
const saving = ref(false)
const listError = ref('')
const modalError = ref('')
const users = ref([])
const showModal = ref(false)

const roleOptions = [
  { value: ROLES.ADMIN, label: 'Administrator' },
  { value: ROLES.INSTRUCTOR, label: 'Instructor' },
  { value: ROLES.LEARNER, label: 'Learner' }
]

const form = reactive({
  email: '',
  password: '',
  full_name: '',
  role: ROLES.LEARNER
})

const resetForm = () => {
  form.email = ''
  form.password = ''
  form.full_name = ''
  form.role = ROLES.LEARNER
}

const loadUsers = async () => {
  loading.value = true
  listError.value = ''
  try {
    users.value = await fetchUsers()
  } catch (e) {
    listError.value = e.message || 'Failed to load users'
    users.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

const openAdd = () => {
  resetForm()
  modalError.value = ''
  showModal.value = true
}

const closeModal = () => {
  if (!saving.value) showModal.value = false
}

const submitCreate = async () => {
  saving.value = true
  modalError.value = ''
  try {
    await createUser({
      email: form.email.trim(),
      password: form.password,
      full_name: form.full_name.trim(),
      role: form.role
    })
    showModal.value = false
    resetForm()
    await loadUsers()
  } catch (e) {
    modalError.value = e.message || 'Could not create user'
  } finally {
    saving.value = false
  }
}

const roleBadgeClass = (roleName) => {
  if (roleName === ROLES.ADMIN) return 'bg-blue-100 text-blue-800'
  if (roleName === ROLES.INSTRUCTOR) return 'bg-purple-100 text-purple-800'
  return 'bg-teal-100 text-teal-800'
}

const hasRows = computed(() => users.value.length > 0)
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <UsersIcon :size="26" class="text-blue-600" />
          Users
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          Create accounts and assign a role. New users can sign in on the login page with the same credentials.
        </p>
      </div>
      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 shadow-sm transition-colors"
        @click="openAdd"
      >
        <Plus :size="18" />
        Add user
      </button>
    </div>

    <div
      v-if="listError && !showModal"
      class="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
    >
      {{ listError }}
    </div>

    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20 text-gray-500 gap-2">
        <Loader2 :size="22" class="animate-spin" />
        Loading users…
      </div>

      <div v-else-if="!hasRows" class="py-16 text-center text-gray-500 text-sm">
        No users yet. Click <strong>Add user</strong> to create one.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Name</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Email</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-700">Role</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="u in users"
              :key="u.id"
              class="border-b border-gray-100 hover:bg-gray-50/80"
            >
              <td class="px-4 py-3 text-gray-900 font-medium">{{ u.full_name || '—' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ u.email }}</td>
              <td class="px-4 py-3">
                <span
                  v-for="r in u.roles"
                  :key="r"
                  :class="['inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium mr-1', roleBadgeClass(r)]"
                >
                  <Shield :size="12" />
                  {{ r }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md border border-gray-100">
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 class="text-lg font-bold text-gray-900">Add user</h2>
            <button
              type="button"
              class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500"
              :disabled="saving"
              @click="closeModal"
            >
              <X :size="20" />
            </button>
          </div>

          <form class="p-5 space-y-4" @submit.prevent="submitCreate">
            <div v-if="modalError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {{ modalError }}
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Full name</label>
              <input
                v-model="form.full_name"
                type="text"
                required
                autocomplete="name"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
                placeholder="Jane Doe"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                v-model="form.email"
                type="email"
                required
                autocomplete="email"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
                placeholder="jane@example.com"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                v-model="form.password"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
                placeholder="At least 8 characters"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                v-model="form.role"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
              >
                <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <button
                type="button"
                class="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100"
                :disabled="saving"
                @click="closeModal"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-60"
                :disabled="saving"
              >
                <Loader2 v-if="saving" :size="16" class="animate-spin" />
                Create user
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>
