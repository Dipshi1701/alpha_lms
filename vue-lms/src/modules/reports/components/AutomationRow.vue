<script setup>
import { computed } from 'vue'
import { Play, Clock, Users2, ToggleLeft, ToggleRight, Pencil, Trash2, Zap } from 'lucide-vue-next'
import clsx from 'clsx'
import { AUTOMATION_TYPES } from '../../../data/appData.js'

const props = defineProps({
  auto: { type: Object, required: true },
})

const emit = defineEmits(['toggle', 'edit', 'delete'])

const type = computed(() => AUTOMATION_TYPES.find(t => t.id === props.auto.typeId))
</script>

<template>
  <div
    :class="clsx(
      'bg-white rounded-xl border transition-all hover:shadow-sm',
      auto.active ? 'border-gray-100' : 'border-gray-100 opacity-70'
    )"
  >
    <div class="flex items-center gap-4 p-4">
      <!-- Icon -->
      <div
        :class="clsx('w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0', type?.bg || 'bg-gray-100')"
      >
        <component
          :is="type?.icon || Zap"
          :size="18"
          :class="type?.color || 'text-gray-500'"
        />
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-0.5">
          <p class="text-sm font-semibold text-gray-800">{{ auto.name }}</p>
          <span
            v-if="type"
            :class="clsx('text-xs font-medium px-2 py-0.5 rounded-full', type.bg, type.color)"
          >
            {{ type.category }}
          </span>
        </div>
        <p class="text-xs text-gray-500 truncate">{{ type?.label || 'Unknown automation type' }}</p>
        <div class="flex items-center gap-4 mt-1.5 text-xs text-gray-400">
          <span class="flex items-center gap-1"><Play :size="10" /> {{ auto.runs }} runs</span>
          <span class="flex items-center gap-1"><Clock :size="10" /> Last run: {{ auto.lastRun }}</span>
          <span v-if="auto.filter" class="flex items-center gap-1"><Users2 :size="10" /> Filter: {{ auto.filter }}</span>
        </div>
      </div>

      <!-- Toggle + actions -->
      <div class="flex items-center gap-2 flex-shrink-0">
        <button @click="emit('toggle')" :title="auto.active ? 'Deactivate' : 'Activate'">
          <ToggleRight v-if="auto.active" :size="26" class="text-green-500" />
          <ToggleLeft v-else :size="26" class="text-gray-300" />
        </button>
        <button
          @click="emit('edit')"
          class="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-500 transition-colors"
          title="Edit"
        >
          <Pencil :size="14" />
        </button>
        <button
          @click="emit('delete')"
          class="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
          title="Delete"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>

    <!-- Active status bar -->
    <div
      :class="clsx('h-0.5 rounded-b-xl transition-all', auto.active ? 'bg-green-400' : 'bg-transparent')"
    />
  </div>
</template>
