<script setup>
import { inject, ref, computed } from 'vue'

const appStore = inject('appStore')

const editingPath = ref(null)
const view = ref('list')

const courses = computed(() => appStore.state.courses)
const paths = computed(() => appStore.state.paths)

const handleCreate = (data) => {
  const path = appStore.createPath(data)
  editingPath.value = path
}

const handleUpdate = (updated) => {
  appStore.updatePath(updated)
  editingPath.value = updated
}

const handleDelete = (id) => {
  appStore.deletePath(id)
}
</script>

<template>
  <div class="p-6 max-w-[1200px] mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-xl font-bold text-gray-800">Learning paths</h1>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ paths.length }} paths • {{ courses.length }} courses
        </p>
      </div>
      <button
        class="px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a] transition-all shadow-sm"
        @click="handleCreate({ name: 'New Path', code: 'NEW', category: 'General', color: 'bg-blue-500', description: '' })"
      >
        + Create path
      </button>
    </div>

    <p class="text-sm text-gray-500 mb-3">
      This Vue page mirrors the Learning Paths list/editor concept from React. You can extend it
      by porting `LearningPathsList` and `LearningPathEditor` widgets into Vue components.
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="path in paths"
        :key="path.id"
        class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
        @click="editingPath = path"
      >
        <div class="flex items-start gap-3 mb-2">
          <div
            :class="`w-9 h-9 rounded-xl ${path.color} flex items-center justify-center text-white font-bold`"
          >
            {{ path.name[0] }}
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-sm font-semibold text-gray-800 truncate">
              {{ path.name }}
            </h2>
            <p class="text-xs text-gray-400">
              {{ path.category }} • {{ (path.courseIds || []).length }} courses
            </p>
          </div>
        </div>
        <p class="text-xs text-gray-500 line-clamp-2">
          {{ path.description }}
        </p>
        <div class="mt-3 flex items-center justify-between text-xs text-gray-400">
          <span>{{ path.createdAt }}</span>
          <span
            :class="[
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full',
              path.active ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'
            ]"
          >
            <span
              :class="[
                'w-1.5 h-1.5 rounded-full',
                path.active ? 'bg-green-500' : 'bg-gray-300'
              ]"
            />
            {{ path.active ? 'Active' : 'Inactive' }}
          </span>
        </div>
      </div>
    </div>

    <div
      v-if="editingPath"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 class="text-base font-semibold text-gray-800">Edit learning path</h2>
            <p class="text-xs text-gray-500 mt-0.5">Basic inline editor placeholder</p>
          </div>
          <button
            class="text-sm text-gray-400 hover:text-gray-600"
            @click="editingPath = null"
          >
            ✕
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1">Name</label>
            <input
              v-model="editingPath.name"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">Code</label>
              <input
                v-model="editingPath.code"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">Category</label>
              <input
                v-model="editingPath.category"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              />
            </div>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-500 mb-1">Description</label>
            <textarea
              v-model="editingPath.description"
              rows="3"
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            />
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 flex justify-between">
          <button
            class="px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg"
            @click="() => { handleDelete(editingPath.id); editingPath = null }"
          >
            Delete path
          </button>
          <div class="space-x-2">
            <button
              class="px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 rounded-lg"
              @click="editingPath = null"
            >
              Cancel
            </button>
            <button
              class="px-4 py-2 text-sm font-semibold text-white bg-[#1a3a5c] rounded-lg hover:bg-[#162f4a]"
              @click="() => { handleUpdate(editingPath); editingPath = null }"
            >
              Save changes
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

