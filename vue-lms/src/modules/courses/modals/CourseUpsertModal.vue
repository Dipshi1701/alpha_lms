<script setup>
import { reactive, ref, watch } from 'vue'
import { X, Upload, Archive, Loader2, ShieldAlert } from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'create' }, // 'create' | 'edit'
  categories: { type: Array, required: true },
  initialValue: { type: Object, default: () => ({}) },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  title: '',
  category: 'General',
  status: 'Draft',
  description: '',
  selectedFileName: '',
})
const formErrors = reactive({
  title: '',
  category: '',
  status: '',
  description: '',
  scormFile: '',
})

watch(
  () => [props.open, props.initialValue],
  () => {
    if (!props.open) return
    form.title = props.initialValue?.title || ''
    form.category = props.initialValue?.category || 'General'
    form.status = props.initialValue?.status || 'Draft'
    form.description = props.initialValue?.description || ''  
    form.selectedFileName = ''
    scormFileRef.value = null
    formErrors.title = ''
    formErrors.category = ''
    formErrors.status = ''
    formErrors.description = ''
    formErrors.scormFile = ''
  },
  { deep: true }
)

const scormFileRef = ref(null)

const onScormFileChange = (event) => {
  const [file] = event.target.files || []
  scormFileRef.value = file || null
  form.selectedFileName = file ? file.name : ''
  formErrors.scormFile = ''
}

const submit = () => {
  if (props.saving) return
  formErrors.title = form.title.trim() ? '' : 'Course title is required'
  formErrors.category = form.category ? '' : 'Category is required'
  formErrors.status = form.status ? '' : 'Status is required'
  formErrors.description = form.description.trim() ? '' : 'Description is required'
  formErrors.scormFile =
    props.mode === 'create' && !scormFileRef.value ? 'SCORM ZIP file is required' : ''

  if (
    formErrors.title ||
    formErrors.category ||
    formErrors.status ||
    formErrors.description ||
    formErrors.scormFile
  ) {
    return
  }

  emit('save', {
    title: form.title.trim(),
    category: form.category,
    status: form.status,
    description: form.description.trim(),
    scormZipName: form.selectedFileName,
    scormFile: scormFileRef.value,
  })
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div class="w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-asi-border flex flex-col">
      <div class="px-6 py-4 border-b border-asi-border flex items-center justify-between">
        <div>
          <h2 class="text-base font-semibold text-asi-black">
            {{ mode === 'edit' ? 'Edit course' : 'Add course' }}
          </h2>
        </div>
        <button
          @click="emit('close')"
          :disabled="saving"
          class="p-1.5 rounded-lg hover:bg-asi-surface text-asi-gray"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-5 overflow-y-auto min-h-[200px]">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-asi-gray mb-1.5">Course title</label>
            <input
              v-model="form.title"
              :disabled="saving"
              required
              placeholder="e.g. Workplace Safety Basics"
              class="w-full px-3 py-2 text-sm border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender text-asi-black"
            />
            <p v-if="formErrors.title" class="mt-1 text-xs text-red-600">{{ formErrors.title }}</p>
          </div>
          <div>
            <label class="block text-xs font-semibold text-asi-gray mb-1.5">Category</label>
            <select
              v-model="form.category"
              :disabled="saving"
              required
              class="w-full px-3 py-2 text-sm bg-white border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender text-asi-black"
            >
              <option
                v-for="cat in categories.filter((c) => c !== 'All')"
                :key="cat"
                :value="cat"
              >
                {{ cat }}
              </option>
            </select>
            <p v-if="formErrors.category" class="mt-1 text-xs text-red-600">{{ formErrors.category }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-asi-gray mb-1.5">Status</label>
            <select
              v-model="form.status"
              :disabled="saving"
              required
              class="w-full px-3 py-2 text-sm bg-white border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender text-asi-black"
            >
              <option value="Draft">Draft</option>
              <option value="Published">Published</option>
            </select>
            <p v-if="formErrors.status" class="mt-1 text-xs text-red-600">{{ formErrors.status }}</p>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-asi-gray mb-1.5">Description</label>
          <textarea
            v-model="form.description"
            :disabled="saving"
            required
            rows="3"
            placeholder="Short overview shown to learners..."
            class="w-full px-3 py-2 text-sm border border-asi-border rounded-lg focus:outline-none focus:ring-2 focus:ring-asi-purple/20 focus:border-asi-lavender text-asi-black"
          />
          <p v-if="formErrors.description" class="mt-1 text-xs text-red-600">{{ formErrors.description }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-asi-gray mb-1.5">Content type</label>
            <div class="w-full px-3 py-2 text-sm bg-asi-surface border border-asi-border rounded-lg text-asi-gray">
              SCORM 1.2 (ZIP) — v0
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-asi-gray mb-1.5">Upload SCORM ZIP</label>
            <label
              class="flex items-center gap-2 px-3 py-2 text-sm border border-dashed border-asi-border rounded-lg cursor-pointer hover:border-asi-lavender hover:bg-asi-purple-light/30 transition-colors"
            >
              <Upload :size="14" class="text-asi-gray" />
              <span class="text-asi-gray">
                {{ form.selectedFileName || 'Choose a .zip file' }}
              </span>
              <input
                type="file"
                accept=".zip,application/zip"
                class="hidden"
                :disabled="saving"
                required
                @change="onScormFileChange"
              />
            </label>
            <p v-if="formErrors.scormFile" class="mt-1 text-xs text-red-600">{{ formErrors.scormFile }}</p>
          </div>
        </div>

        <div class="rounded-xl border px-4 py-3 text-sm flex items-start gap-2 border-asi-border bg-asi-purple-light text-asi-purple">
          <Archive :size="15" class="mt-0.5 flex-shrink-0" />
          <p>
            After save, the ZIP is validated and extracted on the server. Publish only works once SCORM is valid.
          </p>
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
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-asi-purple rounded-lg hover:bg-[#5a3a8a] transition-colors disabled:opacity-60"
        >
          <Loader2 v-if="saving" :size="15" class="animate-spin" />
          {{ saving ? 'Saving...' : mode === 'edit' ? 'Save changes' : 'Create course' }}
        </button>
      </div>
    </div>
  </div>
</template>

