<script setup>
import { ref, computed } from 'vue'
import { Zap, Plus, Search } from 'lucide-vue-next'
import AutomationRow from '../components/AutomationRow.vue'
import AutomationModal from '../components/AutomationModal.vue'
import { INITIAL_AUTOMATIONS } from '../../../data/appData.js'

const automations  = ref(INITIAL_AUTOMATIONS.map(a => ({ ...a })))
const showModal    = ref(false)
const editingAuto  = ref(null)
const search       = ref('')
const confirmDelete = ref(null)

const filtered = computed(() =>
  automations.value.filter(a => a.name.toLowerCase().includes(search.value.toLowerCase()))
)

const activeCount = computed(() => automations.value.filter(a => a.active).length)
const totalRuns   = computed(() => automations.value.reduce((s, a) => s + a.runs, 0))

function toggleActive(id) {
  const a = automations.value.find(a => a.id === id)
  if (a) a.active = !a.active
}

function deleteAuto(id) {
  automations.value = automations.value.filter(a => a.id !== id)
  confirmDelete.value = null
}

function saveAuto(data) {
  if (data.id) {
    const idx = automations.value.findIndex(a => a.id === data.id)
    if (idx !== -1) automations.value[idx] = data
  } else {
    automations.value.push({ ...data, id: Date.now(), runs: 0, lastRun: 'Never' })
  }
  showModal.value = false
  editingAuto.value = null
}

function openEdit(auto) {
  editingAuto.value = auto
  showModal.value = true
}

function openCreate() {
  editingAuto.value = null
  showModal.value = true
}

const summaryCards = computed(() => [
  { label: 'Total Automations', value: automations.value.length, color: 'bg-blue-50 text-blue-600' },
  { label: 'Active',            value: activeCount.value,         color: 'bg-green-50 text-green-600' },
  { label: 'Total Runs',        value: totalRuns.value,           color: 'bg-purple-50 text-purple-600' },
  { label: 'Inactive',          value: automations.value.length - activeCount.value, color: 'bg-gray-100 text-gray-500' },
])
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">

    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Zap :size="20" class="text-amber-500" />
          Automations
        </h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ automations.length }} automation{{ automations.length !== 1 ? 's' : '' }} · {{ activeCount }} active
        </p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-all shadow-sm"
      >
        <Plus :size="15" />
        Add automation
      </button>
    </div>

    <!-- Info banner -->
    <div class="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6 text-sm text-amber-800">
      <Zap :size="16" class="mt-0.5 flex-shrink-0 text-amber-500" />
      <div>
        <p class="font-semibold mb-0.5">How Automations Work</p>
        <p class="text-amber-700/90">
          Automations trigger specific actions (like assigning a course or deactivating a user)
          based on events (like course completion or signup). Set up rules once — Alpha Learn handles the rest automatically.
        </p>
      </div>
    </div>

    <!-- Search -->
    <div class="flex items-center gap-3 mb-5">
      <div class="relative flex-1 max-w-sm">
        <Search :size="15" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          v-model="search"
          placeholder="Search automations..."
          class="w-full pl-9 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
        />
      </div>
    </div>

    <!-- Automation list -->
    <div v-if="filtered.length > 0" class="space-y-3">
      <AutomationRow
        v-for="auto in filtered"
        :key="auto.id"
        :auto="auto"
        @toggle="toggleActive(auto.id)"
        @edit="openEdit(auto)"
        @delete="confirmDelete = auto"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="bg-white rounded-xl border-2 border-dashed border-gray-200 p-16 text-center">
      <div class="w-14 h-14 rounded-2xl bg-amber-50 flex items-center justify-center mx-auto mb-4">
        <Zap :size="26" class="text-amber-400" />
      </div>
      <h3 class="text-base font-semibold text-gray-700 mb-2">
        {{ search ? 'No automations match your search' : 'No automations yet' }}
      </h3>
      <p class="text-sm text-gray-400 max-w-sm mx-auto mb-6">
        {{ search
          ? 'Try a different search term.'
          : 'Create your first automation to start saving time. Set up rules that trigger actions automatically.' }}
      </p>
      <button
        v-if="!search"
        @click="openCreate"
        class="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-colors mx-auto"
      >
        <Plus :size="15" />
        Add automation
      </button>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
      <div
        v-for="card in summaryCards"
        :key="card.label"
        class="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3"
      >
        <div :class="`w-10 h-10 rounded-xl ${card.color} flex items-center justify-center font-bold text-lg`">
          {{ card.value }}
        </div>
        <p class="text-sm font-medium text-gray-600">{{ card.label }}</p>
      </div>
    </div>

    <!-- Create / Edit modal -->
    <AutomationModal
      v-if="showModal"
      :automation="editingAuto"
      @save="saveAuto"
      @close="showModal = false; editingAuto = null"
    />

    <!-- Delete confirm dialog -->
    <div
      v-if="confirmDelete"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm">
        <h3 class="text-base font-semibold text-gray-800 mb-2">Delete Automation?</h3>
        <p class="text-sm text-gray-500 mb-5">
          Deleting <strong>"{{ confirmDelete.name }}"</strong> will permanently remove this automation and it cannot be restored.
        </p>
        <div class="flex gap-3">
          <button
            @click="confirmDelete = null"
            class="flex-1 px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            @click="deleteAuto(confirmDelete.id)"
            class="flex-1 px-4 py-2 text-sm font-semibold text-white bg-red-500 rounded-lg hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
