<script setup>
import { ref, computed } from 'vue'
import { Zap, X, Save, Search, CheckCircle2 } from 'lucide-vue-next'
import clsx from 'clsx'
import { AUTOMATION_TYPES, AUTOMATION_MOCK_COURSES, AUTOMATION_MOCK_LPS, AUTOMATION_CATEGORIES } from '../../../data/appData.js'

const props = defineProps({
  automation: { type: Object, default: null },
})

const emit = defineEmits(['save', 'close'])

const name     = ref(props.automation?.name    || '')
const typeId   = ref(props.automation?.typeId  || '')
const params   = ref({ ...(props.automation?.params || {}) })
const filter   = ref(props.automation?.filter  || '')
const filterType      = ref('none')
const searchType      = ref('')
const selectedCategory = ref('All')

const selectedType = computed(() => AUTOMATION_TYPES.find(t => t.id === typeId.value))

function setParam(key, val) {
  params.value = { ...params.value, [key]: val }
}

function clearType() {
  typeId.value = ''
  params.value = {}
}

function pickType(id) {
  typeId.value = id
  params.value = {}
}

function handleSave() {
  if (!name.value.trim() || !typeId.value) return
  emit('save', {
    ...(props.automation || {}),
    name: name.value.trim(),
    typeId: typeId.value,
    params: params.value,
    filter: filter.value || null,
    active: props.automation?.active ?? true,
  })
}

const filteredTypes = computed(() =>
  AUTOMATION_TYPES.filter(t => {
    const matchSearch = t.label.toLowerCase().includes(searchType.value.toLowerCase())
    const matchCat = selectedCategory.value === 'All' || t.category === selectedCategory.value
    return matchSearch && matchCat
  })
)
</script>

<template>
  <div class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 flex-shrink-0">
        <h2 class="text-base font-semibold text-gray-800 flex items-center gap-2">
          <Zap :size="16" class="text-amber-500" />
          {{ automation ? 'Edit Automation' : 'Add Automation' }}
        </h2>
        <button @click="emit('close')" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400">
          <X :size="18" />
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-6 space-y-5">

        <!-- Name -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">
            Automation name <span class="text-red-500">*</span>
          </label>
          <input
            v-model="name"
            placeholder="e.g. New hire onboarding sequence"
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
          />
        </div>

        <!-- Automation type picker -->
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">
            Automation type <span class="text-red-500">*</span>
          </label>

          <!-- Selected type display -->
          <div
            v-if="selectedType"
            :class="clsx('flex items-center gap-3 p-3 rounded-xl border-2 border-blue-400 mb-3', selectedType.bg)"
          >
            <component :is="selectedType.icon" :size="18" :class="selectedType.color" />
            <div class="flex-1 min-w-0">
              <p :class="clsx('text-xs font-semibold', selectedType.color)">{{ selectedType.category }}</p>
              <p class="text-sm font-medium text-gray-700 leading-tight">{{ selectedType.label }}</p>
            </div>
            <button @click="clearType" class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0">
              <X :size="15" />
            </button>
          </div>
          <div v-else class="border border-dashed border-gray-300 rounded-xl p-3 text-center text-sm text-gray-400 mb-3">
            Select an automation type below
          </div>

          <!-- Type browser -->
          <div class="border border-gray-200 rounded-xl overflow-hidden">
            <!-- Search + category filter -->
            <div class="p-3 border-b border-gray-100 bg-gray-50 space-y-2">
              <div class="relative">
                <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  v-model="searchType"
                  placeholder="Search automation types..."
                  class="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400"
                />
              </div>
              <div class="flex gap-1.5 flex-wrap">
                <button
                  v-for="cat in AUTOMATION_CATEGORIES"
                  :key="cat"
                  @click="selectedCategory = cat"
                  :class="clsx(
                    'px-2.5 py-1 text-xs font-medium rounded-full border transition-all',
                    selectedCategory === cat
                      ? 'bg-[#1a3a5c] text-white border-[#1a3a5c]'
                      : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'
                  )"
                >
                  {{ cat }}
                </button>
              </div>
            </div>

            <!-- Type list -->
            <div class="max-h-48 overflow-y-auto divide-y divide-gray-50">
              <button
                v-for="type in filteredTypes"
                :key="type.id"
                @click="pickType(type.id)"
                :class="clsx(
                  'flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors',
                  typeId === type.id ? 'bg-blue-50' : ''
                )"
              >
                <div :class="clsx('w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0', type.bg)">
                  <component :is="type.icon" :size="14" :class="type.color" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs text-gray-700 leading-snug">{{ type.label }}</p>
                </div>
                <CheckCircle2 v-if="typeId === type.id" :size="14" class="text-blue-500 flex-shrink-0" />
              </button>
              <div v-if="filteredTypes.length === 0" class="py-6 text-center text-xs text-gray-400">
                No matching automation types
              </div>
            </div>
          </div>
        </div>

        <!-- Dynamic param fields -->
        <div v-if="selectedType && selectedType.params.length > 0" class="bg-gray-50 rounded-xl p-4 space-y-4">
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Configure Parameters</p>

          <!-- Z — hours -->
          <div v-if="selectedType.params.includes('hours_z')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">Z</span> — Number of hours
            </label>
            <input
              type="number"
              :min="1"
              :value="params.hours_z || ''"
              @input="setParam('hours_z', $event.target.value)"
              placeholder="e.g. 24"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
          </div>

          <!-- X — course trigger -->
          <div v-if="selectedType.params.includes('course_x')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">X</span> — Course (trigger)
            </label>
            <select
              :value="params.course_x || ''"
              @change="setParam('course_x', $event.target.value)"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select a course...</option>
              <option v-for="c in AUTOMATION_MOCK_COURSES" :key="c">{{ c }}</option>
            </select>
          </div>

          <!-- Y — courses to assign -->
          <div v-if="selectedType.params.includes('courses_y')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">Y</span> — Course(s) to assign
            </label>
            <select
              :value="params.courses_y || ''"
              @change="setParam('courses_y', $event.target.value)"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select a course...</option>
              <option v-for="c in AUTOMATION_MOCK_COURSES" :key="c">{{ c }}</option>
            </select>
          </div>

          <!-- X — learning path trigger -->
          <div v-if="selectedType.params.includes('lp_x')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">X</span> — Learning path (trigger)
            </label>
            <select
              :value="params.lp_x || ''"
              @change="setParam('lp_x', $event.target.value)"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select a learning path...</option>
              <option v-for="l in AUTOMATION_MOCK_LPS" :key="l">{{ l }}</option>
            </select>
          </div>

          <!-- Y — learning paths to assign -->
          <div v-if="selectedType.params.includes('lps_y')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">Y</span> — Learning path(s) to assign
            </label>
            <select
              :value="params.lps_y || ''"
              @change="setParam('lps_y', $event.target.value)"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select a learning path...</option>
              <option v-for="l in AUTOMATION_MOCK_LPS" :key="l">{{ l }}</option>
            </select>
          </div>

          <!-- K / L — score range -->
          <div v-if="selectedType.params.includes('score_k')" class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">
                <span class="font-bold text-blue-600">K</span> — Min score (%)
              </label>
              <input
                type="number" :min="0" :max="100"
                :value="params.score_k || ''"
                @input="setParam('score_k', $event.target.value)"
                placeholder="0"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">
                <span class="font-bold text-blue-600">L</span> — Max score (%)
              </label>
              <input
                type="number" :min="0" :max="100"
                :value="params.score_l || ''"
                @input="setParam('score_l', $event.target.value)"
                placeholder="100"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <!-- Action — deactivate / delete -->
          <div v-if="selectedType.params.includes('action_deactivate_delete')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Action</label>
            <div class="flex gap-3">
              <label
                v-for="action in ['deactivate', 'delete']"
                :key="action"
                :class="clsx(
                  'flex items-center gap-2 flex-1 p-3 rounded-lg border cursor-pointer transition-all capitalize',
                  params.action_deactivate_delete === action
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                )"
              >
                <input
                  type="radio"
                  name="action"
                  :value="action"
                  :checked="params.action_deactivate_delete === action"
                  @change="setParam('action_deactivate_delete', action)"
                  class="text-blue-600"
                />
                <span class="text-sm font-medium text-gray-700 capitalize">{{ action }} user</span>
              </label>
            </div>
          </div>

          <!-- Z — webhook URL -->
          <div v-if="selectedType.params.includes('url_z')">
            <label class="block text-sm font-medium text-gray-700 mb-1.5">
              <span class="font-bold text-blue-600">Z</span> — Webhook URL
            </label>
            <input
              type="url"
              :value="params.url_z || ''"
              @input="setParam('url_z', $event.target.value)"
              placeholder="https://example.com/webhook"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
          </div>
        </div>

        <!-- Filter (optional) -->
        <div v-if="selectedType?.supportsFilter" class="border border-gray-200 rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-gray-700">Filter (optional)</p>
            <select
              v-model="filterType"
              class="text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white focus:outline-none"
            >
              <option value="none">No filter</option>
              <option value="branch">By Branch</option>
              <option value="group">By Group</option>
              <option value="usertype">By User Type</option>
            </select>
          </div>
          <select
            v-if="filterType !== 'none'"
            v-model="filter"
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">Select {{ filterType }}...</option>
            <template v-if="filterType === 'branch'">
              <option v-for="b in ['US Branch', 'EU Branch', 'APAC Branch']" :key="b">{{ b }}</option>
            </template>
            <template v-if="filterType === 'group'">
              <option v-for="g in ['Sales Team', 'Engineering', 'HR']" :key="g">{{ g }}</option>
            </template>
            <template v-if="filterType === 'usertype'">
              <option v-for="u in ['Learners', 'Instructors', 'Administrators']" :key="u">{{ u }}</option>
            </template>
          </select>
        </div>

      </div>

      <!-- Footer -->
      <div class="flex gap-3 px-6 py-4 border-t border-gray-100 flex-shrink-0">
        <button
          @click="emit('close')"
          class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          :disabled="!name.trim() || !typeId"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Save :size="14" />
          {{ automation ? 'Save changes' : 'Create automation' }}
        </button>
      </div>

    </div>
  </div>
</template>
