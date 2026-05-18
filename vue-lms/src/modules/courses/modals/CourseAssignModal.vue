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
    <div class="w-full max-w-xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
      <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
        <div>
          <h2 class="text-base font-semibold text-asi-black">Assign course</h2>
          <p class="text-xs text-asi-gray mt-0.5">
            {{ courseTitle }}
          </p>
        </div>
        <button
          @click="emit('close')"
          class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-3 overflow-y-auto min-h-[200px]">
        <div class="flex items-center gap-2">
          <UserPlus :size="14" class="text-asi-gray" />
          <p class="text-sm text-asi-gray">
            Select learners to assign this course.
          </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label
            v-for="u in users"
            :key="u.id"
            class="flex items-center justify-between border border-asi-border rounded-lg px-3 py-2 cursor-pointer hover:border-asi-lavender transition-colors"
          >
            <div>
              <p class="text-sm font-medium text-asi-black">{{ u.name }}</p>
              <p class="text-xs text-asi-gray">{{ u.role }}</p>
            </div>
            <button
              type="button"
              @click="toggleAssignUser(u.id)"
              :class="clsx(
                'text-xs font-semibold px-2 py-1 rounded-md border',
                form.assignedUserIds.includes(u.id)
                  ? 'bg-asi-purple text-white border-asi-purple'
                  : 'bg-white text-asi-gray border-asi-border'
              )"
            >
              {{ form.assignedUserIds.includes(u.id) ? 'Assigned' : 'Assign' }}
            </button>
          </label>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
        <button
          @click="emit('close')"
          class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg"
        >
          Cancel
        </button>
        <button
          @click="submit"
          class="px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] transition-colors"
        >
          Save assignment
        </button>
      </div>
    </div>
  </div>
</template>

