<script setup>
import { reactive, watch } from 'vue'
import { X, UserPlus } from 'lucide-vue-next'
import clsx from 'clsx'

const props = defineProps({
  open: { type: Boolean, default: false },
  courseTitle: { type: String, default: '' },
  users: { type: Array, required: true }, // [{id,name,role}]
  initialAssignedUserIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  assignedUserIds: [],
})

watch(
  () => [props.open, props.initialAssignedUserIds],
  () => {
    if (!props.open) return
    form.assignedUserIds = [...(props.initialAssignedUserIds || [])]
  },
  { deep: true }
)

const toggleAssignUser = (userId) => {
  if (form.assignedUserIds.includes(userId)) {
    form.assignedUserIds = form.assignedUserIds.filter((id) => id !== userId)
    return
  }
  form.assignedUserIds = [...form.assignedUserIds, userId]
}

const submit = () => {
  emit('save', { assignedUserIds: [...form.assignedUserIds] })
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 class="text-base font-semibold text-gray-800">Assign course</h2>
          <p class="text-xs text-gray-500 mt-0.5">
            {{ courseTitle }}
          </p>
        </div>
        <button
          @click="emit('close')"
          class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-3 overflow-y-auto min-h-[200px]">
        <div class="flex items-center gap-2">
          <UserPlus :size="14" class="text-gray-500" />
          <p class="text-sm text-gray-700">
            Select learners to assign this course.
          </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label
            v-for="u in users"
            :key="u.id"
            class="flex items-center justify-between border border-gray-200 rounded-lg px-3 py-2 cursor-pointer hover:border-blue-300 transition-colors"
          >
            <div>
              <p class="text-sm font-medium text-gray-700">{{ u.name }}</p>
              <p class="text-xs text-gray-400">{{ u.role }}</p>
            </div>
            <button
              type="button"
              @click="toggleAssignUser(u.id)"
              :class="clsx(
                'text-xs font-semibold px-2 py-1 rounded-md border',
                form.assignedUserIds.includes(u.id)
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-300'
              )"
            >
              {{ form.assignedUserIds.includes(u.id) ? 'Assigned' : 'Assign' }}
            </button>
          </label>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
        <button
          @click="emit('close')"
          class="px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          Cancel
        </button>
        <button
          @click="submit"
          class="px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-colors"
        >
          Save assignment
        </button>
      </div>
    </div>
  </div>
</template>

