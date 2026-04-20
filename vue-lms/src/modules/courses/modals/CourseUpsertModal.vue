<script setup>
import { reactive, ref, watch } from 'vue'
import { X, Upload, Archive, Loader2 } from 'lucide-vue-next'

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
    <div class="w-full max-w-2xl max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col">
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 class="text-base font-semibold text-gray-800">
            {{ mode === 'edit' ? 'Edit course' : 'Add course' }}
          </h2>
          <p class="text-xs text-gray-500 mt-0.5">
            SCORM 1.2 ZIP — validated on upload
          </p>
        </div>
        <button
          @click="emit('close')"
          :disabled="saving"
          class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400"
        >
          <X :size="18" />
        </button>
      </div>

      <div class="p-6 space-y-5 overflow-y-auto min-h-[200px]">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1.5">Course title</label>
            <input
              v-model="form.title"
              :disabled="saving"
              required
              placeholder="e.g. Workplace Safety Basics"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
            <p v-if="formErrors.title" class="mt-1 text-xs text-red-600">{{ formErrors.title }}</p>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1.5">Category</label>
            <select
              v-model="form.category"
              :disabled="saving"
              required
              class="w-full px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
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
            <label class="block text-xs font-semibold text-gray-500 mb-1.5">Status</label>
            <select
              v-model="form.status"
              :disabled="saving"
              required
              class="w-full px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            >
              <option value="Draft">Draft</option>
              <option value="Published">Published</option>
            </select>
            <p v-if="formErrors.status" class="mt-1 text-xs text-red-600">{{ formErrors.status }}</p>
          </div>
          <div class="hidden md:block" />
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1.5">Description</label>
          <textarea
            v-model="form.description"
            :disabled="saving"
            required
            rows="3"
            placeholder="Short overview shown to learners..."
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
          />
          <p v-if="formErrors.description" class="mt-1 text-xs text-red-600">{{ formErrors.description }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1.5">Content type</label>
            <div class="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg text-gray-700">
              SCORM 1.2 (ZIP) — v0
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1.5">Upload SCORM ZIP</label>
            <label
              class="flex items-center gap-2 px-3 py-2 text-sm border border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-300 hover:bg-blue-50/40 transition-colors"
            >
              <Upload :size="14" class="text-gray-500" />
              <span class="text-gray-600">
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

        <div class="rounded-xl border px-4 py-3 text-sm flex items-start gap-2 border-purple-200 bg-purple-50 text-purple-700">
          <Archive :size="15" class="mt-0.5 flex-shrink-0" />
          <p>
            After save, the ZIP is validated and extracted on the server. Publish only works once SCORM is valid.
          </p>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
        <button
          @click="emit('close')"
          :disabled="saving"
          class="px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          Cancel
        </button>
        <button
          @click="submit"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-colors disabled:opacity-60"
        >
          <Loader2 v-if="saving" :size="15" class="animate-spin" />
          {{ saving ? 'Saving...' : mode === 'edit' ? 'Save changes' : 'Create course' }}
        </button>
      </div>
    </div>
  </div>
</template>

