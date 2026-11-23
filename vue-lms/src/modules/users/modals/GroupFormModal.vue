<script setup>
import { reactive, watch } from 'vue'
import { X, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'create' }, // 'create' | 'edit'
  initialValue: { type: Object, default: () => ({}) },
  saving: { type: Boolean, default: false },
  apiError: { type: String, default: '' },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  name: '',
})
const formErrors = reactive({
  name: '',
})

watch(
  () => [props.open, props.initialValue],
  () => {
    if (!props.open) return
    form.name = props.initialValue?.name || ''
    formErrors.name = ''
  },
  { deep: true }
)

const submit = () => {
  if (props.saving) return
  formErrors.name = form.name.trim() ? '' : 'Group name is required'
  if (formErrors.name) return
  emit('save', { name: form.name.trim() })
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div class="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
      <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
        <h2 class="text-base font-semibold text-asi-black">
          {{ mode === 'edit' ? 'Edit group' : 'Create group' }}
        </h2>
        <button
          @click="emit('close')"
          :disabled="saving"
          class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-4">
        <div v-if="apiError" class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          {{ apiError }}
        </div>

        <div>
          <label class="block text-xs font-semibold text-asi-gray mb-1.5">Group name</label>
          <input
            v-model="form.name"
            data-testid="group-name-input"
            :disabled="saving"
            required
            placeholder="e.g. Frontend Batch"
            class="w-full px-3 py-2 text-sm border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender text-asi-black"
            @keyup.enter="submit"
          />
          <p v-if="formErrors.name" class="mt-1 text-xs text-red-600">{{ formErrors.name }}</p>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-asi-border flex items-center justify-end gap-2">
        <button
          @click="emit('close')"
          :disabled="saving"
          class="px-3 py-2 text-sm font-medium text-asi-gray hover:bg-asi-surface rounded-lg"
        >
          Cancel
        </button>
        <button
          @click="submit"
          data-testid="group-form-submit"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] transition-colors disabled:opacity-60"
        >
          <Loader2 v-if="saving" :size="15" class="animate-spin" />
          {{ saving ? 'Saving...' : mode === 'edit' ? 'Save changes' : 'Create group' }}
        </button>
      </div>
    </div>
  </div>
</template>
