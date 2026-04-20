<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="p-6 flex flex-col items-center justify-center min-h-[50vh] text-center">
    <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
      <span class="text-xl">📄</span>
    </div>
    <h1 class="text-xl font-bold text-gray-700 mb-1">{{ props.title }}</h1>
    <p class="text-sm text-gray-400">This section is ready for your content.</p>
  </div>
</template>

